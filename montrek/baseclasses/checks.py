"""Startup checks for the per-app access policy and the navigation built on it.

Restricting an app (see ``baseclasses.access``) only holds if every view in it
ends up behind a permission. These turn the two ways that can quietly fail - an
app slipping out of a restricted subtree, and a view slipping past the gate -
into startup errors. Silent for open apps.

The last one guards the other direction: the navigation hides an entry it cannot
resolve, so a mistyped ``NAVBAR_APPS`` entry would silently disappear from every
menu instead of failing. It is reported here instead.
"""

from django.apps import apps
from django.core.checks import Error, Tags, register
from django.core.exceptions import ImproperlyConfigured
from django.urls import URLPattern, URLResolver, get_resolver

from baseclasses.access import (
    UNCONFIGURED_PERMISSION,
    AccessKind,
    declared_access_policy,
    permissions_for_callback,
    resolve_app_policy,
    route_for_url_name,
)
from baseclasses.app_config import (
    NAMESPACE_ATTRIBUTE,
    declaring_namespace_class,
    is_below_namespace,
)
from baseclasses.navigation import navigation_url_names


def _namespace_owners() -> dict[str, type]:
    """Each claimed dotted path, mapped to the class claiming it.

    A path claimed twice belongs to the first claimant, the same choice
    find_namespace_base makes, so an app is checked against the base the
    generator would have given it.
    """
    owners: dict[str, type] = {}
    for app_config in apps.get_app_configs():
        namespace = getattr(app_config, NAMESPACE_ATTRIBUTE, None)
        declaring_class = declaring_namespace_class(app_config)
        if namespace and declaring_class is not None:
            owners.setdefault(namespace, declaring_class)
    return owners


@register(Tags.security)
def check_claimed_namespaces(app_configs=None, **kwargs) -> list[Error]:
    """Every app below a claimed namespace must use that namespace's config.

    Without this, adding an app inside a restricted subtree and giving it a
    plain ``AppConfig`` would leave it wide open while everything around it is
    gated, and nothing about the new app would look wrong.
    """
    errors = []
    owners = _namespace_owners()
    for app_config in apps.get_app_configs():
        for namespace, declaring_class in owners.items():
            if not is_below_namespace(app_config.name, namespace):
                continue
            if isinstance(app_config, declaring_class):
                continue
            errors.append(
                Error(
                    f"App {app_config.name!r} lies below the namespace "
                    f"{namespace!r} but its app config does not inherit from "
                    f"{declaring_class.__module__}.{declaring_class.__qualname__}.",
                    hint=(
                        "Inherit the app's config from that class, and keep "
                        "'default = True' on the config itself."
                    ),
                    obj=app_config,
                    id="montrek.E001",
                )
            )
    return errors


@register(Tags.security)
def check_access_policy_declarations(app_configs=None, **kwargs) -> list[Error]:
    """Every app config's access policy must be one the resolver understands.

    Registered rather than left to the resolver, which raises: that exception
    would surface mid-way through the URL walk below, aborting the checks run
    instead of reporting, and would never reach an app that routes no URLs.
    """
    errors = []
    for app_config in apps.get_app_configs():
        try:
            declared_access_policy(app_config)
        except ImproperlyConfigured as error:
            errors.append(Error(str(error), obj=app_config, id="montrek.E005"))
    return errors


def _urlconf_module(resolver) -> str:
    """Dotted name of the module a resolver's patterns came from.

    ``include()`` also accepts a bare list, which has no module of its own and
    inherits its parent's.
    """
    urlconf_name = getattr(resolver, "urlconf_name", None)
    if isinstance(urlconf_name, str):
        return urlconf_name
    return getattr(urlconf_name, "__name__", "")


def _iter_url_patterns(resolver=None, urlconf_module=""):
    """Every ``URLPattern`` from the root URLconf, with the module routing it."""
    resolver = resolver or get_resolver()
    module = _urlconf_module(resolver) or urlconf_module
    try:
        url_patterns = resolver.url_patterns
    except Exception:
        # A broken URLconf is reported by Django's own url checks.
        return
    for pattern in url_patterns:
        if isinstance(pattern, URLResolver):
            yield from _iter_url_patterns(pattern, module)
        elif isinstance(pattern, URLPattern):
            yield pattern, module


@register(Tags.security)
def check_restricted_app_views(app_configs=None, **kwargs) -> list[Error]:
    """No view routed from a restricted app may be reachable without a
    permission.

    In scope when either the view's own module or the ``urls.py`` routing it is
    restricted. Those differ when an app routes a class living outside it, and
    the gate resolves only the class' module - so it would grant access to
    everybody while the app around it is locked down.
    """
    errors: list[Error] = []
    seen: set = set()
    for pattern, urlconf_module in _iter_url_patterns():
        try:
            errors.extend(_pattern_errors(pattern, urlconf_module, seen))
        except ImproperlyConfigured:
            # An access_policy the resolver cannot read, already reported as
            # montrek.E005. Skipped rather than raised so that this check still
            # reports every other route.
            continue
    return errors


def _pattern_errors(pattern, urlconf_module: str, seen: set) -> list[Error]:
    """The errors one routed pattern is responsible for, if any."""
    from baseclasses.views import MontrekPermissionRequiredMixin

    callback = pattern.callback
    view_class = getattr(callback, "view_class", None)
    initkwargs = getattr(callback, "view_initkwargs", {}) or {}
    target = view_class if view_class is not None else callback
    module = getattr(target, "__module__", "")
    key = (target, urlconf_module, initkwargs.get("access_module"))
    if not module or key in seen:
        return []
    seen.add(key)
    if not (
        resolve_app_policy(urlconf_module).is_restricted
        or resolve_app_policy(module).is_restricted
    ):
        return []

    name = f"{module}.{getattr(target, '__qualname__', target)}"
    if view_class is None or not issubclass(view_class, MontrekPermissionRequiredMixin):
        return [
            Error(
                f"{name} is routed from a restricted app but carries no "
                f"permission gate.",
                hint=(
                    "Use a Montrek base view, or mix in "
                    "MontrekPermissionRequiredMixin and set 'access_kind'."
                ),
                obj=name,
                id="montrek.E003",
            )
        ]

    permissions = permissions_for_callback(callback)
    if not permissions:
        return [
            Error(
                f"{name} is routed from the restricted app {urlconf_module!r}, "
                f"but its view class lives outside that app, so the gate "
                f"resolves to no permission.",
                hint=(
                    "Pass 'access_module=__name__' from the app's urls.py, "
                    "declare 'permission_required', or move the class into the "
                    "app."
                ),
                obj=name,
                id="montrek.E003",
            )
        ]
    if UNCONFIGURED_PERMISSION in permissions:
        access_kind = getattr(view_class, "access_kind", AccessKind.VIEW)
        return [
            Error(
                f"{name} needs a permission for access kind "
                f"{access_kind.value!r}, but its app configures none.",
                hint=(
                    "Add that access kind to the app config's "
                    "'access_permissions' mapping."
                ),
                obj=name,
                id="montrek.E004",
            )
        ]
    return []


@register(Tags.security)
def check_navigation_entries(app_configs=None, **kwargs) -> list[Error]:
    """Every ``NAVBAR_APPS`` entry must resolve to a view.

    The navigation filters itself down to what its user may reach, and an entry
    whose URL name will not reverse resolves to a permission nobody holds - so
    it is hidden from everybody, which looks exactly like a missing permission.
    Without this check a typo in ``.env`` would be invisible until somebody
    noticed a menu item was gone.
    """
    return [
        Error(
            f"Navigation entry {url_name!r} does not resolve to a view, so it "
            f"is hidden from every user.",
            hint=(
                "Fix the entry in the NAVBAR_APPS setting: its last dotted "
                "segment is the name of a URL pattern that takes no arguments."
            ),
            obj=f"NAVBAR_APPS: {url_name}",
            id="montrek.E006",
        )
        for url_name in navigation_url_names()
        if route_for_url_name(url_name) is None
    ]


@register(Tags.security)
def check_object_scope_is_enforced(app_configs=None, **kwargs) -> list[Error]:
    """A view declaring ``object_scope_permissions`` must actually check them.

    That attribute is a *declaration*, not a gate. It tells callers reasoning
    about a view without issuing a request - the test harness above all - which
    permissions a request may additionally need; the check itself has to live in
    the view's own ``has_permission``, because which of them applies depends on
    the object the URL names, which is not known until the request arrives.

    A view that declares the attribute and inherits ``has_permission`` unchanged
    would therefore read as object scoped while enforcing nothing, and the test
    harness would hand its user the permissions to match - so nothing would fail.
    That is the one way this contract can be silently empty, and it is what this
    turns into a startup error.
    """
    from django.contrib.auth.mixins import PermissionRequiredMixin

    errors: list[Error] = []
    seen: set = set()
    for pattern, _ in _iter_url_patterns():
        view_class = getattr(pattern.callback, "view_class", None)
        if view_class is None or view_class in seen:
            continue
        seen.add(view_class)
        if not getattr(view_class, "object_scope_permissions", ()):
            continue
        if view_class.has_permission is not PermissionRequiredMixin.has_permission:
            continue
        name = f"{view_class.__module__}.{view_class.__qualname__}"
        errors.append(
            Error(
                f"{name} declares 'object_scope_permissions' but does not "
                f"override 'has_permission', so nothing checks them.",
                hint=(
                    "Mix in a view that resolves the object and checks the "
                    "matching permission - see FundScopeMixin - or drop the "
                    "declaration."
                ),
                obj=name,
                id="montrek.E007",
            )
        )
    return errors

"""Startup checks for the per-app access policy.

Restricting an app (see ``baseclasses.access``) only holds if every view in it
ends up behind a permission. These turn the two ways that can quietly fail - an
app slipping out of a restricted subtree, and a view slipping past the gate -
into startup errors. Silent for open apps.
"""

from django.apps import apps
from django.core.checks import Error, Tags, register
from django.core.exceptions import ImproperlyConfigured
from django.urls import URLPattern, URLResolver, get_resolver

from baseclasses.access import (
    UNCONFIGURED_PERMISSION,
    AccessKind,
    declared_access_policy,
    permissions_for_view,
    resolve_app_policy,
)
from baseclasses.app_config import (
    NAMESPACE_ATTRIBUTE,
    declaring_namespace_class,
    is_below_namespace,
)


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


def _effective_permissions(view_class: type, initkwargs: dict) -> tuple[str, ...]:
    """What the gate would require, without instantiating the view.

    ``initkwargs`` are the arguments the URLconf passed to ``as_view``, which is
    where a shared view is told which app's policy applies to it - see
    ``MontrekNavigationRedirectView.access_module``.
    """
    # Presence, not truthiness: ``as_view(permission_required=[])`` deliberately
    # clears a class-level permission so the app policy applies, and at runtime
    # the empty instance attribute wins. Reading the class attribute instead
    # would make this check disagree with the gate.
    permission_required = (
        initkwargs["permission_required"]
        if "permission_required" in initkwargs
        else getattr(view_class, "permission_required", None)
    )
    if permission_required:
        # Django accepts a bare string as well as a list, so a plain tuple()
        # here would report the characters of a single permission.
        if isinstance(permission_required, str):
            return (permission_required,)
        return tuple(permission_required)
    access_kind = getattr(view_class, "access_kind", AccessKind.VIEW)
    module = initkwargs.get("access_module") or view_class.__module__
    return permissions_for_view(module, access_kind)


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

    permissions = _effective_permissions(view_class, initkwargs)
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

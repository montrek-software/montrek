"""Startup checks for the per-app access policy.

Restricting an app (see ``baseclasses.access``) only holds if every view in it
actually ends up behind a permission. These checks turn the two ways that can
quietly fail - an app slipping out of a restricted subtree, and a view slipping
past the gate - into startup errors.

They are silent for open apps, so a project that restricts nothing never sees
them.
"""

from django.apps import apps
from django.core.checks import Error, Tags, register
from django.urls import URLPattern, URLResolver, get_resolver

from baseclasses.access import (
    UNCONFIGURED_PERMISSION,
    AccessKind,
    permissions_for_view,
    resolve_app_policy,
)

NAMESPACE_ATTRIBUTE = "namespace"


def _declaring_class(cls: type, attribute: str) -> type | None:
    """The class in ``cls``'s MRO that actually defines ``attribute``.

    An app config inherits ``namespace`` from the base its subtree shares, and
    that base - not the leaf config - is what the other apps have to use.
    """
    for klass in cls.__mro__:
        if attribute in klass.__dict__:
            return klass
    return None


def _claimed_namespaces() -> dict[str, list[type]]:
    """Every dotted path claimed by an app config base, mapped to the bases
    claiming it."""
    claims: dict[str, list[type]] = {}
    for app_config in apps.get_app_configs():
        namespace = getattr(app_config, NAMESPACE_ATTRIBUTE, None)
        if not namespace:
            continue
        declaring_class = _declaring_class(type(app_config), NAMESPACE_ATTRIBUTE)
        if declaring_class is None:
            continue
        claiming = claims.setdefault(namespace, [])
        if declaring_class not in claiming:
            claiming.append(declaring_class)
    return claims


def _is_below(app_name: str, namespace: str) -> bool:
    return app_name == namespace or app_name.startswith(f"{namespace}.")


@register(Tags.security)
def check_claimed_namespaces(app_configs=None, **kwargs) -> list[Error]:
    """Every app below a claimed namespace must use that namespace's config.

    Without this, adding an app inside a restricted subtree and giving it a
    plain ``AppConfig`` would leave it wide open while everything around it is
    gated - and nothing about the new app would look wrong.
    """
    errors = []
    for namespace, declaring_classes in sorted(_claimed_namespaces().items()):
        if len(declaring_classes) > 1:
            names = ", ".join(
                f"{klass.__module__}.{klass.__qualname__}"
                for klass in declaring_classes
            )
            errors.append(
                Error(
                    f"Several app config classes claim the namespace "
                    f"{namespace!r}: {names}.",
                    hint=(
                        "A namespace has one owner. Keep the claim on the base "
                        "the subtree's apps inherit from and remove the others."
                    ),
                    id="montrek.E002",
                )
            )
            continue
        declaring_class = declaring_classes[0]
        for app_config in apps.get_app_configs():
            if not _is_below(app_config.name, namespace):
                continue
            if isinstance(app_config, declaring_class):
                continue
            errors.append(
                Error(
                    f"App {app_config.name!r} lies below the namespace "
                    f"{namespace!r} but its app config does not inherit from "
                    f"{declaring_class.__module__}.{declaring_class.__qualname__}.",
                    hint=(
                        "Inherit the app's config from that class so it picks "
                        "up the subtree's access policy, and keep "
                        "'default = True' on the config itself."
                    ),
                    obj=app_config,
                    id="montrek.E001",
                )
            )
    return errors


def _urlconf_module(resolver) -> str:
    """Dotted name of the module a resolver's patterns were included from.

    ``include()`` accepts a bare list of patterns as well as a module; such a
    resolver has no module of its own and inherits the one of its parent.
    """
    urlconf_name = getattr(resolver, "urlconf_name", None)
    if isinstance(urlconf_name, str):
        return urlconf_name
    return getattr(urlconf_name, "__name__", "")


def _iter_url_patterns(resolver=None, urlconf_module=""):
    """Every ``URLPattern`` reachable from the root URLconf, paired with the
    module it was routed from."""
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


def _effective_permissions(view_class: type) -> tuple[str, ...]:
    """What the gate would require, resolved from class attributes only.

    Mirrors ``MontrekPermissionRequiredMixin.get_permission_required`` without
    instantiating the view - including the fact that it resolves the policy
    from the view class' own module, not from wherever the view is routed.
    """
    permission_required = getattr(view_class, "permission_required", None)
    if permission_required:
        return tuple(permission_required)
    access_kind = getattr(view_class, "access_kind", AccessKind.VIEW)
    return permissions_for_view(view_class.__module__, access_kind)


@register(Tags.security)
def check_restricted_app_views(app_configs=None, **kwargs) -> list[Error]:
    """No view routed from a restricted app may be reachable without a
    permission.

    A view is in scope when either its own module or the ``urls.py`` routing it
    belongs to a restricted app. The two differ when an app routes a view class
    that lives outside it - in a helper package without an ``apps.py``, say, or
    in a neighbouring app. The gate resolves the policy from the view class'
    module alone, so in that case it grants access to everybody while the app
    around it is locked down, which is exactly the silent hole worth reporting.
    """
    from baseclasses.views import MontrekPermissionRequiredMixin

    errors = []
    seen: set = set()
    for pattern, urlconf_module in _iter_url_patterns():
        callback = pattern.callback
        view_class = getattr(callback, "view_class", None)
        target = view_class if view_class is not None else callback
        module = getattr(target, "__module__", "")
        if not module or (target, urlconf_module) in seen:
            continue
        seen.add((target, urlconf_module))
        routed_from_restricted_app = resolve_app_policy(urlconf_module).is_restricted
        if not (routed_from_restricted_app or resolve_app_policy(module).is_restricted):
            continue
        name = f"{module}.{getattr(target, '__qualname__', target)}"
        if view_class is None or not issubclass(
            view_class, MontrekPermissionRequiredMixin
        ):
            errors.append(
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
            )
            continue
        permissions = _effective_permissions(view_class)
        if not permissions:
            errors.append(
                Error(
                    f"{name} is routed from the restricted app "
                    f"{urlconf_module!r}, but its view class lives outside "
                    f"that app, so the gate resolves to no permission.",
                    hint=(
                        "Declare 'permission_required' on the view, or move "
                        "the class into the restricted app."
                    ),
                    obj=name,
                    id="montrek.E003",
                )
            )
        elif UNCONFIGURED_PERMISSION in permissions:
            access_kind = getattr(view_class, "access_kind", AccessKind.VIEW)
            errors.append(
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
            )
    return errors

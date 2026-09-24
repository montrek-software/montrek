"""Base ``AppConfig`` carrying an app's access policy.

Apart from ``baseclasses/apps.py`` so importing the base does not drag in the
``baseclasses`` app config, and so that module keeps one autodiscovery
candidate. See ``baseclasses.access`` for what the policy does.
"""

from typing import cast

from django.apps import AppConfig, apps
from django.core.exceptions import ImproperlyConfigured

from baseclasses.access import AccessKind, AccessPolicy, NamespacedPermission

# Attribute an app config base uses to claim a dotted path for its subtree.
NAMESPACE_ATTRIBUTE = "namespace"


class MontrekAppConfig(AppConfig):
    """``AppConfig`` base that lets an app declare its access policy.

    ``default = False`` keeps this base out of Django's autodiscovery, which
    refuses to choose between two candidates in one ``apps.py``.

    The exclusion is inherited, so a concrete config **must** set
    ``default = True``: without it Django finds no candidate and falls back to a
    plain ``AppConfig``, dropping the access policy silently.
    ``__init_subclass__`` makes that an import-time error.
    """

    default = False
    default_auto_field = "django.db.models.BigAutoField"

    # Access policy, see baseclasses.access. Both attributes are inherited, so
    # a subtree can declare them once on a shared base and its apps pick them
    # up by inheriting from that base.
    access_policy: AccessPolicy = AccessPolicy.OPEN
    access_permissions: dict[AccessKind, NamespacedPermission] = {}

    # Dotted path a shared base claims for its subtree. Checked at startup:
    # every installed app below the namespace must use that base.
    namespace: str | None = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        is_concrete_app_config = "name" in cls.__dict__
        if is_concrete_app_config and cls.__dict__.get("default") is not True:
            raise ImproperlyConfigured(
                f"{cls.__module__}.{cls.__qualname__} sets 'name' and is "
                f"therefore an app config Django has to discover, but it does "
                f"not set 'default = True'. It inherits 'default = False' from "
                f"MontrekAppConfig, which would make Django ignore it and fall "
                f"back to a plain AppConfig, silently dropping the app's "
                f"access policy. Add 'default = True' to the class."
            )
        cls._raise_for_nested_namespaces()

    @classmethod
    def _raise_for_nested_namespaces(cls) -> None:
        """Namespaces are siblings, never nested.

        Everything that reads a claim - ``declaring_namespace_class``,
        ``find_namespace_base``, the montrek.E001 check - takes the one claim a
        config has. With two claims in one MRO they would silently see only the
        inner one, leaving the outer subtree unenforced. Supporting nesting means
        walking the MRO in all three places, so it is refused here instead until
        something actually needs it.
        """
        claims = [
            base for base in cls.__mro__ if base.__dict__.get(NAMESPACE_ATTRIBUTE)
        ]
        if len(claims) > 1:
            claimed = ", ".join(
                f"{base.__qualname__} claims {base.__dict__[NAMESPACE_ATTRIBUTE]!r}"
                for base in claims
            )
            raise ImproperlyConfigured(
                f"{cls.__module__}.{cls.__qualname__} inherits more than one "
                f"namespace claim ({claimed}), and nested namespaces are not "
                f"supported: only the innermost would be enforced. Keep the "
                f"claims siblings, or teach declaring_namespace_class, "
                f"find_namespace_base and check_claimed_namespaces to walk the "
                f"MRO."
            )


def is_below_namespace(app_name: str, namespace: str) -> bool:
    """Whole path segments only, so ``a_other`` is not below ``a``."""
    return app_name == namespace or app_name.startswith(f"{namespace}.")


def declaring_namespace_class(app_config) -> type[MontrekAppConfig] | None:
    """The class claiming this app config's namespace.

    The claim sits on the base a subtree's apps share, and that base - not the
    leaf config - is what the subtree's other apps have to inherit from.
    """
    namespace = getattr(app_config, NAMESPACE_ATTRIBUTE, None)
    if not namespace:
        return None
    klass = app_config if isinstance(app_config, type) else type(app_config)
    # Only MontrekAppConfig and its subclasses declare a namespace.
    return cast(
        type[MontrekAppConfig] | None,
        next(
            (base for base in klass.__mro__ if NAMESPACE_ATTRIBUTE in base.__dict__),
            None,
        ),
    )


def find_namespace_base(app_name: str) -> type[MontrekAppConfig] | None:
    """The app config base of the innermost namespace ``app_name`` falls into.

    The innermost, because ``_raise_for_nested_namespaces`` only refuses two
    claims in one class hierarchy: two independent configs can still claim ``a``
    and ``a.b``. Taking the first match would then let app registration order
    decide which policy a generated app inherits.

    ``None`` outside every claimed namespace, so the app has to bring its own
    access policy.
    """
    candidates = []
    for app_config in apps.get_app_configs():
        namespace = getattr(app_config, NAMESPACE_ATTRIBUTE, None)
        declaring_class = declaring_namespace_class(app_config)
        if namespace and declaring_class and is_below_namespace(app_name, namespace):
            candidates.append((namespace, declaring_class))
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: len(candidate[0]))[1]

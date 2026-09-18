"""Base ``AppConfig`` carrying an app's access policy.

Lives apart from ``baseclasses/apps.py`` so that importing the base never drags
in the ``baseclasses`` app config itself, and so that ``baseclasses/apps.py``
keeps exactly one ``AppConfig`` candidate for Django's autodiscovery.

See ``baseclasses.access`` for what the policy does.
"""

from django.apps import AppConfig, apps
from django.core.exceptions import ImproperlyConfigured

from baseclasses.access import AccessKind, AccessPolicy, NamespacedPermission

# Attribute an app config base uses to claim a dotted path for its subtree.
NAMESPACE_ATTRIBUTE = "namespace"


class MontrekAppConfig(AppConfig):
    """``AppConfig`` base that lets an app declare its access policy.

    ``default = False`` keeps this base out of Django's autodiscovery: it
    inspects every ``AppConfig`` subclass reachable in an app's ``apps.py``,
    imported names included, and refuses to choose between two candidates.

    That exclusion is inherited, so a concrete app config **must** set
    ``default = True`` itself.  Without it Django finds no candidate at all and
    silently falls back to a plain ``AppConfig`` - the app would keep working
    while losing its access policy.  ``__init_subclass__`` below turns that
    silent downgrade into an error at import time.
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


def is_below_namespace(app_name: str, namespace: str) -> bool:
    """Whether ``app_name`` lies inside ``namespace``.

    Matches whole path segments only, so ``test_subtree_other`` is not below
    ``test_subtree``.
    """
    return app_name == namespace or app_name.startswith(f"{namespace}.")


def declaring_namespace_class(app_config) -> type | None:
    """The class in an app config's MRO that actually claims its namespace.

    An app config inherits ``namespace`` from the base its subtree shares, and
    that base - not the leaf config - is what the subtree's other apps have to
    inherit from.
    """
    if not getattr(app_config, NAMESPACE_ATTRIBUTE, None):
        return None
    for klass in type(app_config).__mro__:
        if NAMESPACE_ATTRIBUTE in klass.__dict__:
            return klass
    return None


def find_namespace_base(app_name: str) -> type | None:
    """The app config base claiming the namespace ``app_name`` would fall into.

    ``None`` when the app lies outside every claimed namespace and therefore
    has to bring its own access policy.
    """
    for app_config in apps.get_app_configs():
        namespace = getattr(app_config, NAMESPACE_ATTRIBUTE, None)
        if not namespace or not is_below_namespace(app_name, namespace):
            continue
        declaring_class = declaring_namespace_class(app_config)
        if declaring_class is not None:
            return declaring_class
    return None

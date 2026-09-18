"""Per-app access policy for Montrek views.

Montrek's historical default is *open*: a view lets everybody through unless it
declares its own ``permission_required``.  ``MontrekPermissionRequiredMixin``
keeps that default, but an app can reverse it for itself by declaring

    class FooConfig(MontrekAppConfig):
        name = "some.package.foo"
        default = True
        access_policy = AccessPolicy.RESTRICTED
        access_permissions = {
            AccessKind.VIEW: FooPermissions.CAN_VIEW,
            AccessKind.CREATE: FooPermissions.CAN_CREATE,
            AccessKind.UPDATE: FooPermissions.CAN_UPDATE,
            AccessKind.DELETE: FooPermissions.CAN_DELETE,
        }

Every view in a restricted app then needs a permission: the one its
``access_kind`` maps to, unless the view names an explicit
``permission_required``, which always wins.  Apps that say nothing stay open,
so adding this module changes nothing for existing apps.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from functools import cache
from typing import Protocol

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

# Handed out when a restricted app has no permission configured for the access
# kind a view asks for.  No such permission is ever created in the database, so
# the request is denied instead of silently waved through - a misconfigured app
# must not be more permissive than a configured one.  The startup checks report
# the misconfiguration; this constant only keeps the gate closed until it is
# fixed.
UNCONFIGURED_PERMISSION = "montrek.access_policy_not_configured"


class AccessPolicy(Enum):
    """What an app does with a view that declares no permission of its own."""

    OPEN = "open"
    RESTRICTED = "restricted"


class AccessKind(Enum):
    """The kind of access a view grants, mapped to a permission per app."""

    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class NamespacedPermission(Protocol):
    """A permission enum member as used across the Montrek apps.

    An app declares its permissions as an enum whose members carry a
    ``namespaced_codename``: the ``"<app_label>.<codename>"`` string
    ``User.has_perms`` expects.
    """

    namespaced_codename: str


@dataclass(frozen=True)
class AppAccessPolicy:
    """The resolved access policy of a single app."""

    policy: AccessPolicy = AccessPolicy.OPEN
    permissions: Mapping[AccessKind, NamespacedPermission] = field(default_factory=dict)
    app_label: str = ""

    @property
    def is_restricted(self) -> bool:
        return self.policy is AccessPolicy.RESTRICTED

    def permissions_for(self, access_kind: AccessKind) -> tuple[str, ...]:
        """The permissions a view of ``access_kind`` needs in this app.

        Empty for an open app - that is the historical "everybody may" default.
        """
        if not self.is_restricted:
            return ()
        permission = self.permissions.get(access_kind)
        if permission is None:
            logger.error(
                "App %r is restricted but configures no permission for access "
                "kind %r; denying access.",
                self.app_label,
                access_kind.value,
            )
            return (UNCONFIGURED_PERMISSION,)
        # getattr rather than attribute access: a misconfigured app must deny,
        # not raise. Raising here would also abort the startup checks, which
        # resolve permissions through this method to report the very same
        # misconfiguration.
        codename = getattr(permission, "namespaced_codename", "")
        if not codename:
            logger.error(
                "The permission app %r maps to access kind %r has no "
                "'namespaced_codename' (%r); denying access.",
                self.app_label,
                access_kind.value,
                permission,
            )
            return (UNCONFIGURED_PERMISSION,)
        return (codename,)


OPEN_POLICY = AppAccessPolicy()


def declared_access_policy(app_config) -> AccessPolicy:
    """The ``access_policy`` of an app config, as an ``AccessPolicy``.

    A plain string is accepted and converted, since ``access_policy =
    "restricted"`` is the obvious thing to write. Anything that is not a policy
    raises instead of being read as "open": a typo must not be able to turn the
    gate off, and treating an unknown value as the permissive one would do
    exactly that, silently and without the startup checks noticing either.
    """
    policy = getattr(app_config, "access_policy", AccessPolicy.OPEN)
    if isinstance(policy, AccessPolicy):
        return policy
    try:
        return AccessPolicy(policy)
    except ValueError as error:
        app_label = getattr(app_config, "label", app_config)
        valid = ", ".join(repr(member.value) for member in AccessPolicy)
        raise ImproperlyConfigured(
            f"App {app_label!r} declares access_policy={policy!r}, which is "
            f"not an access policy. Use AccessPolicy.OPEN / "
            f"AccessPolicy.RESTRICTED, or one of {valid}."
        ) from error


def declared_access_permissions(app_config) -> dict:
    """The ``access_permissions`` of an app config as a mapping.

    Anything that will not convert is reported and treated as empty rather than
    raised: an empty mapping leaves every access kind unconfigured, which denies
    access and is reported by the montrek.E004 check, while an exception here
    would reach the user as a 500 and would abort that check before it could
    report anything.
    """
    declared = getattr(app_config, "access_permissions", {})
    try:
        return dict(declared)
    except (TypeError, ValueError):
        logger.error(
            "App %r declares access_permissions that are not a mapping (%r); "
            "treating them as empty, which denies every access kind.",
            getattr(app_config, "label", app_config),
            declared,
        )
        return {}


@cache
def resolve_app_policy(module: str) -> AppAccessPolicy:
    """The access policy of the app ``module`` belongs to.

    ``module`` is a view class' ``__module__``.  Modules outside any installed
    app - shared base classes, helper packages without an ``apps.py`` - have no
    app config and therefore stay open.
    """
    app_config = apps.get_containing_app_config(module)
    if app_config is None:
        return OPEN_POLICY
    policy = declared_access_policy(app_config)
    if policy is not AccessPolicy.RESTRICTED:
        return OPEN_POLICY
    return AppAccessPolicy(
        policy=policy,
        permissions=declared_access_permissions(app_config),
        app_label=app_config.label,
    )


def permissions_for_view(module: str, access_kind: AccessKind) -> tuple[str, ...]:
    """The default permissions for a view in ``module`` accessed as
    ``access_kind``."""
    return resolve_app_policy(module).permissions_for(access_kind)


def clear_access_policy_cache() -> None:
    """Drop the resolution cache.  App configs do not change at runtime, so
    this is only needed by tests that swap a policy in."""
    resolve_app_policy.cache_clear()

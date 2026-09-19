"""Per-app access policy for Montrek views.

Montrek's default is open: a view lets everybody through unless it declares its
own ``permission_required``. An app reverses that for itself by declaring
``access_policy = AccessPolicy.RESTRICTED`` on its ``MontrekAppConfig``, plus an
``access_permissions`` mapping from ``AccessKind`` to a permission enum member.
Every view in it then needs the permission its ``access_kind`` maps to, unless
it names a ``permission_required``, which always wins. Apps that say nothing
stay open.
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

# Handed out when a restricted app maps no permission to the access kind a view
# asks for. Never created in the database, so the request is denied rather than
# waved through: a misconfigured app must not be more permissive than a
# configured one. The montrek.E004 check reports it at startup.
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
    """A permission enum member: ``namespaced_codename`` is the
    ``"<app_label>.<codename>"`` string ``User.has_perms`` expects."""

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
        """The permissions a view of ``access_kind`` needs. Empty for an open
        app, which is the "everybody may" default."""
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
        # not raise. Raising would also abort the startup checks, which resolve
        # permissions through here to report that very misconfiguration.
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

    A matching string is converted. Anything else raises rather than being read
    as "open": a typo must not be able to turn the gate off silently.
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

    Anything that will not convert is logged and treated as empty: that leaves
    every access kind unconfigured, which denies and is reported by
    montrek.E004, where raising would be a 500 and would abort that check.
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

    ``module`` is a view class' ``__module__``. Modules outside any installed
    app - shared bases, packages without an ``apps.py`` - stay open.
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
    """Drop the resolution cache. Only needed by tests that swap a policy in."""
    resolve_app_policy.cache_clear()

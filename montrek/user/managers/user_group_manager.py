"""Materialising declared user groups and their permissions.

A group is declared as an enum member carrying a ``group_name`` and a list of
permission enum members - see the ``*UserGroups`` enums in the extension apps.
This turns such a declaration into ``Group`` and ``Permission`` rows.

The permissions are model independent: they gate views, not objects, so they
hang off one placeholder ``ContentType`` per declaring app rather than off a
model of their own.
"""

import logging

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)


def create_permission(permission) -> Permission:
    """The ``Permission`` row a declared permission enum member stands for."""
    content_type, _ = ContentType.objects.get_or_create(
        app_label=permission.app_label, model=permission.model
    )
    permission_obj, _ = Permission.objects.get_or_create(
        name=permission.permission_name,
        content_type=content_type,
        codename=permission.codename,
    )
    return permission_obj


def create_groups(group_enum) -> None:
    """Create or update every group declared by ``group_enum``."""
    for group in group_enum:
        group_obj, _ = Group.objects.get_or_create(name=group.group_name)
        permission_objs = [
            create_permission(permission) for permission in group.permissions
        ]
        # set() rather than add(): permissions dropped from a group in the enum
        # must also disappear from the group in the database.
        group_obj.permissions.set(permission_objs)
        logger.info(
            "Group %r now carries %d permission(s).",
            group.group_name,
            len(permission_objs),
        )

"""Create the user groups declared by the given group enums.

    python manage.py runscript setup_user_groups --script-args \\
        my_app.user_groups.constants.MyUserGroups \\
        other_app.user_groups.constants.OtherUserGroups

Needed as a step of its own because a group's permissions only exist in the
database once some group declares them: an app whose access policy maps to a
permission nobody has yet denies everybody. So this runs, and its groups are
assigned, before an app is switched to a restricted access policy.
"""

import logging

from django.utils.module_loading import import_string

from user.managers.user_group_manager import create_groups

logger = logging.getLogger(__name__)


def run(*group_enum_paths: str) -> None:
    if not group_enum_paths:
        raise ValueError(
            "Pass the dotted paths of the group enums to create, e.g. "
            "--script-args my_app.user_groups.constants.MyUserGroups"
        )
    for path in group_enum_paths:
        logger.info("Creating the groups declared by %s.", path)
        create_groups(import_string(path))

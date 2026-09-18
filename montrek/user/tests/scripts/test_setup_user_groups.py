"""The standalone group-creation script.

It exists so that groups can be materialised on their own, before an app is
switched to a restricted access policy - a permission nobody holds denies
everybody, so the grants have to be in place first.
"""

from enum import Enum

from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from user.scripts.setup_user_groups import run


class ScriptTestPermissions(Enum):
    CAN_VIEW = "Kann Testdaten sehen"

    def __init__(self, permission_name: str):
        self.app_label = "script_test"
        self.permission_name = permission_name
        self.codename = permission_name.lower().replace(" ", "_")
        self.namespaced_codename = f"{self.app_label}.{self.codename}"
        self.model = "model independent"


class ScriptTestUserGroups(Enum):
    REVISION = ("Script Test Revision", [ScriptTestPermissions.CAN_VIEW])

    def __init__(self, group_name, permissions):
        self.group_name = group_name
        self.permissions = permissions


GROUP_ENUM_PATH = f"{__name__}.ScriptTestUserGroups"


class TestSetupUserGroupsScript(TestCase):
    def test_creates_the_group_and_its_permission(self):
        run(GROUP_ENUM_PATH)

        group = Group.objects.get(name="Script Test Revision")
        self.assertEqual(
            ["kann_testdaten_sehen"],
            list(group.permissions.values_list("codename", flat=True)),
        )

    def test_is_idempotent(self):
        run(GROUP_ENUM_PATH)
        run(GROUP_ENUM_PATH)

        self.assertEqual(1, Group.objects.filter(name="Script Test Revision").count())
        self.assertEqual(
            1, Permission.objects.filter(codename="kann_testdaten_sehen").count()
        )

    def test_accepts_several_enums_at_once(self):
        run(GROUP_ENUM_PATH, GROUP_ENUM_PATH)

        self.assertEqual(1, Group.objects.filter(name="Script Test Revision").count())

    def test_refuses_to_run_without_an_enum(self):
        with self.assertRaises(ValueError) as ctx:
            run()

        self.assertIn("--script-args", str(ctx.exception))

    def test_unknown_enum_path_is_reported(self):
        with self.assertRaises(ImportError):
            run("nowhere.at.all.Groups")

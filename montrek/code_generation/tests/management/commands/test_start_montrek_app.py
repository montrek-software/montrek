"""start_montrek_app - creating an app forces a decision about its access.

The point of ``--access`` being required is that a new app can no longer end up
open by nobody thinking about it. These tests pin down the three shapes of app
config it writes and the errors that stop a half-created app being left behind.
"""

import importlib.util
import io
import os
import shutil
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from baseclasses.access import AccessPolicy
from baseclasses.app_config import MontrekAppConfig
from code_generation.tests import get_test_file_path

RISK_PERMISSIONS = (
    "mt_competo.risk_management.user_groups.constants.RiskContributorPermissions"
)


class NamespaceBaseConfig(MontrekAppConfig):
    """Stands in for the base a restricted subtree shares."""

    namespace = "test_namespace"
    access_policy = AccessPolicy.RESTRICTED


class OpenNamespaceBaseConfig(MontrekAppConfig):
    """A claimed subtree that keeps its apps open."""

    namespace = "test_open_namespace"
    access_policy = AccessPolicy.OPEN


class StartMontrekAppTestCaseBase(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.output_dir = os.path.relpath(get_test_file_path("start_app_output"))
        shutil.rmtree(self.output_dir, ignore_errors=True)
        os.makedirs(self.output_dir, exist_ok=True)
        self.addCleanup(shutil.rmtree, self.output_dir, ignore_errors=True)

    def call(self, app_name, **options):
        with patch("sys.stdout", new_callable=io.StringIO):
            call_command("start_montrek_app", app_name, path=self.output_dir, **options)
        return os.path.join(self.output_dir, app_name)

    def app_config_source(self, app_path) -> str:
        with open(os.path.join(app_path, "apps.py"), encoding="utf-8") as f:
            return f.read()

    def import_app_config(self, app_path: str, config_cls_name: str) -> type:
        """Import the generated apps.py the way Django would.

        A real import rather than a compiled snippet: it resolves the imports
        the template wrote and runs MontrekAppConfig.__init_subclass__, so the
        test fails on a config Django would silently ignore.
        """
        module_path = os.path.join(app_path, "apps.py")
        spec = importlib.util.spec_from_file_location(
            f"generated_app_config_{config_cls_name}", module_path
        )
        self.assertIsNotNone(spec, f"could not load a module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, config_cls_name)

    @property
    def dotted_output_dir(self) -> str:
        return os.path.normpath(self.output_dir).replace(os.sep, ".")


class TestAccessIsMandatory(StartMontrekAppTestCaseBase):
    def test_creating_an_app_without_deciding_is_refused(self):
        with self.assertRaises(CommandError) as ctx:
            self.call("no_decision")

        self.assertIn("--access", str(ctx.exception))

    def test_nothing_is_created_when_the_decision_is_missing(self):
        with self.assertRaises(CommandError):
            self.call("no_decision")

        self.assertFalse(os.path.exists(os.path.join(self.output_dir, "no_decision")))

    def test_only_the_two_policies_are_accepted(self):
        with self.assertRaises(CommandError):
            self.call("nonsense_policy", access="maybe")


class TestOpenApp(StartMontrekAppTestCaseBase):
    def test_app_config_states_the_open_policy(self):
        app_path = self.call("plain_app", access="open")

        source = self.app_config_source(app_path)
        self.assertIn("class PlainAppConfig(MontrekAppConfig):", source)
        self.assertIn("access_policy = AccessPolicy.OPEN", source)
        self.assertIn(
            f'name = "{self.dotted_output_dir}.plain_app"',
            source,
        )

    def test_app_config_opts_into_django_discovery(self):
        """Inheriting MontrekAppConfig means inheriting 'default = False'."""
        app_path = self.call("plain_app", access="open")

        self.assertIn("default = True", self.app_config_source(app_path))

    def test_generated_app_config_is_importable(self):
        app_path = self.call("plain_app", access="open")

        config_class = self.import_app_config(app_path, "PlainAppConfig")

        self.assertIs(config_class.access_policy, AccessPolicy.OPEN)
        self.assertTrue(config_class.default)

    def test_unwanted_startapp_files_are_removed(self):
        app_path = self.call("plain_app", access="open")

        for removed in ("tests.py", "models.py", "views.py"):
            self.assertFalse(os.path.exists(os.path.join(app_path, removed)))

    def test_permissions_are_rejected_for_an_open_app(self):
        with self.assertRaises(CommandError) as ctx:
            self.call("plain_app", access="open", permissions=RISK_PERMISSIONS)

        self.assertIn("restricted", str(ctx.exception))


class TestRestrictedAppOutsideAnySubtree(StartMontrekAppTestCaseBase):
    def test_permissions_are_required(self):
        with self.assertRaises(CommandError) as ctx:
            self.call("lonely_app", access="restricted")

        self.assertIn("--permissions", str(ctx.exception))

    def test_nothing_is_created_when_permissions_are_missing(self):
        with self.assertRaises(CommandError):
            self.call("lonely_app", access="restricted")

        self.assertFalse(os.path.exists(os.path.join(self.output_dir, "lonely_app")))

    def test_app_config_carries_the_full_permission_mapping(self):
        app_path = self.call(
            "lonely_app", access="restricted", permissions=RISK_PERMISSIONS
        )

        source = self.app_config_source(app_path)
        self.assertIn("access_policy = AccessPolicy.RESTRICTED", source)
        for access_kind in ("VIEW", "CREATE", "UPDATE", "DELETE"):
            self.assertIn(
                f"AccessKind.{access_kind}: "
                f"RiskContributorPermissions.CAN_{access_kind}",
                source,
            )

    def test_generated_app_config_is_importable(self):
        app_path = self.call(
            "lonely_app", access="restricted", permissions=RISK_PERMISSIONS
        )

        config_class = self.import_app_config(app_path, "LonelyAppConfig")

        self.assertIs(config_class.access_policy, AccessPolicy.RESTRICTED)
        self.assertEqual(len(config_class.access_permissions), 4)

    def test_unimportable_permission_enum_is_refused(self):
        with self.assertRaises(CommandError) as ctx:
            self.call(
                "lonely_app",
                access="restricted",
                permissions="nowhere.at.all.Permissions",
            )

        self.assertIn("Could not import", str(ctx.exception))

    def test_permission_enum_missing_an_access_kind_is_refused(self):
        """An unmapped access kind denies everybody, so it is caught here."""
        with self.assertRaises(CommandError) as ctx:
            self.call(
                "lonely_app",
                access="restricted",
                permissions=(
                    "mt_competo.asset_management.user_groups.constants"
                    ".DatevTransactionPermissions"
                ),
            )

        self.assertIn("CAN_VIEW", str(ctx.exception))


class TestRestrictedAppInsideASubtree(StartMontrekAppTestCaseBase):
    """A restricted subtree owns the policy, so its apps only inherit it."""

    def setUp(self):
        super().setUp()
        patcher = patch(
            "code_generation.management.commands.start_montrek_app.find_namespace_base",
            return_value=NamespaceBaseConfig,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_app_config_inherits_the_subtree_base(self):
        app_path = self.call("subtree_app", access="restricted")

        source = self.app_config_source(app_path)
        self.assertIn("class SubtreeAppConfig(NamespaceBaseConfig):", source)
        # ruff wraps a long import, so only the module is matched literally.
        self.assertIn(f"from {NamespaceBaseConfig.__module__} import", source)

    def test_policy_is_not_restated_but_pointed_at(self):
        """Restating it would let the leaf drift from the base it inherits."""
        app_path = self.call("subtree_app", access="restricted")

        source = self.app_config_source(app_path)
        self.assertNotIn("access_policy =", source)
        self.assertNotIn("access_permissions =", source)
        self.assertIn("# Access policy: restricted, inherited from", source)
        self.assertIn(
            "NamespaceBaseConfig, which owns the test_namespace subtree", source
        )

    def test_generated_app_config_is_importable_and_restricted(self):
        app_path = self.call("subtree_app", access="restricted")

        config_class = self.import_app_config(app_path, "SubtreeAppConfig")

        self.assertTrue(issubclass(config_class, NamespaceBaseConfig))
        self.assertIs(config_class.access_policy, AccessPolicy.RESTRICTED)
        self.assertEqual(config_class.namespace, "test_namespace")

    def test_own_permissions_are_refused(self):
        with self.assertRaises(CommandError) as ctx:
            self.call("subtree_app", access="restricted", permissions=RISK_PERMISSIONS)

        self.assertIn("NamespaceBaseConfig", str(ctx.exception))

    def test_open_inside_a_restricted_subtree_is_refused(self):
        """Creating it would produce an app the montrek.E001 check rejects at
        startup, so it is refused before anything is written."""
        with self.assertRaises(CommandError) as ctx:
            self.call("subtree_app", access="open")

        message = str(ctx.exception)
        self.assertIn("NamespaceBaseConfig", message)
        self.assertIn("--access restricted", message)

    def test_nothing_is_created_when_the_policy_contradicts_the_subtree(self):
        with self.assertRaises(CommandError):
            self.call("subtree_app", access="open")

        self.assertFalse(os.path.exists(os.path.join(self.output_dir, "subtree_app")))


class TestOpenSubtree(StartMontrekAppTestCaseBase):
    """A namespace may also be claimed by a base that keeps its apps open."""

    def setUp(self):
        super().setUp()
        patcher = patch(
            "code_generation.management.commands.start_montrek_app.find_namespace_base",
            return_value=OpenNamespaceBaseConfig,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_restricted_inside_an_open_subtree_is_refused(self):
        with self.assertRaises(CommandError) as ctx:
            self.call("subtree_app", access="restricted")

        self.assertIn("--access open", str(ctx.exception))

    def test_open_inside_an_open_subtree_inherits_the_base(self):
        app_path = self.call("subtree_app", access="open")

        source = self.app_config_source(app_path)
        self.assertIn("class SubtreeAppConfig(OpenNamespaceBaseConfig):", source)
        self.assertIn("# Access policy: open, inherited from", source)
        self.assertNotIn("access_policy =", source)

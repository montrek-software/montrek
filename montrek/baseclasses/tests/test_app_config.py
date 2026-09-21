"""MontrekAppConfig - the base an app declares its access policy on.

The interesting part is the ``default`` flag. Django picks an app's config by
inspecting every AppConfig subclass reachable in its ``apps.py`` and skipping
those with ``default = False``; when that leaves no candidate it silently falls
back to a plain ``AppConfig``. A config inheriting ``default = False`` from this
base would therefore lose its access policy without any warning, so the base
refuses to be subclassed that way.
"""

from unittest import mock

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from baseclasses.access import AccessKind, AccessPolicy
from baseclasses.app_config import (
    MontrekAppConfig,
    declaring_namespace_class,
    find_namespace_base,
    is_below_namespace,
)


def declare_app_config(name, bases, attributes):
    """Create an app config class the way importing an ``apps.py`` would.

    Class creation is what runs ``__init_subclass__``, so the refusals below
    happen here. The class itself is never used afterwards.
    """
    return type(name, bases, attributes)


class TestMontrekAppConfigDefaults(TestCase):
    def test_apps_are_open_unless_they_say_otherwise(self):
        self.assertIs(MontrekAppConfig.access_policy, AccessPolicy.OPEN)
        self.assertEqual(MontrekAppConfig.access_permissions, {})
        self.assertIsNone(MontrekAppConfig.namespace)

    def test_base_is_excluded_from_django_autodiscovery(self):
        self.assertFalse(MontrekAppConfig.default)


class TestConcreteConfigMustOptIntoDiscovery(TestCase):
    def test_concrete_config_without_default_true_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured) as ctx:
            declare_app_config(
                "BrokenConfig", (MontrekAppConfig,), {"name": "baseclasses"}
            )

        self.assertIn("default = True", str(ctx.exception))

    def test_concrete_config_with_default_true_is_accepted(self):
        class WorkingConfig(MontrekAppConfig):
            name = "baseclasses"
            default = True

        self.assertTrue(WorkingConfig.default)

    def test_shared_subtree_base_needs_no_default(self):
        """A base without ``name`` is never discovered, so it stays excluded."""

        class SubtreeBase(MontrekAppConfig):
            namespace = "some.subtree"
            access_policy = AccessPolicy.RESTRICTED

        class LeafConfig(SubtreeBase):
            name = "baseclasses"
            default = True

        self.assertIs(LeafConfig.access_policy, AccessPolicy.RESTRICTED)
        self.assertEqual(LeafConfig.namespace, "some.subtree")

    def test_policy_and_permissions_are_inherited(self):
        class SubtreeBase(MontrekAppConfig):
            access_policy = AccessPolicy.RESTRICTED
            access_permissions = {AccessKind.VIEW: object()}

        class LeafConfig(SubtreeBase):
            name = "baseclasses"
            default = True

        self.assertEqual(LeafConfig.access_permissions, SubtreeBase.access_permissions)


# A subtree base and an app inside it.
ROOT_NAMESPACE = "test_subtree"


class SubtreeBaseConfig(MontrekAppConfig):
    namespace = ROOT_NAMESPACE
    access_policy = AccessPolicy.RESTRICTED


class InsideConfig(SubtreeBaseConfig):
    pass


class OutsiderConfig(MontrekAppConfig):
    pass


class TestIsBelowNamespace(TestCase):
    def test_matches_the_namespace_and_what_is_under_it(self):
        self.assertTrue(is_below_namespace(ROOT_NAMESPACE, ROOT_NAMESPACE))
        self.assertTrue(is_below_namespace(f"{ROOT_NAMESPACE}.app", ROOT_NAMESPACE))

    def test_matches_whole_segments_only(self):
        self.assertFalse(is_below_namespace("test_subtree_other", ROOT_NAMESPACE))


class TestDeclaringNamespaceClass(TestCase):
    def test_the_claim_is_attributed_to_the_base_declaring_it(self):
        self.assertIs(declaring_namespace_class(InsideConfig), SubtreeBaseConfig)

    def test_a_config_claiming_nothing_has_no_owner(self):
        self.assertIsNone(declaring_namespace_class(OutsiderConfig))


class TestFindNamespaceBase(TestCase):
    """The generator picks an app's base with this."""

    def _find(self, app_name):
        module = apps.get_app_config("baseclasses").module
        installed = [InsideConfig(f"{ROOT_NAMESPACE}.inside", module)]
        with mock.patch.object(apps, "get_app_configs", return_value=installed):
            return find_namespace_base(app_name)

    def test_app_in_the_subtree_gets_its_base(self):
        self.assertIs(self._find(f"{ROOT_NAMESPACE}.new_app"), SubtreeBaseConfig)

    def test_app_outside_it_gets_nothing(self):
        self.assertIsNone(self._find("somewhere.else.new_app"))


class TestNestedNamespacesAreRefused(TestCase):
    """Everything that reads a claim takes the one claim a config has, so two in
    one MRO would leave the outer subtree unenforced. Refused at import."""

    def test_a_second_claim_in_the_same_hierarchy_is_refused(self):
        with self.assertRaises(ImproperlyConfigured) as ctx:
            declare_app_config(
                "NestedConfig",
                (SubtreeBaseConfig,),
                {"namespace": f"{ROOT_NAMESPACE}.inner"},
            )

        message = str(ctx.exception)
        self.assertIn(ROOT_NAMESPACE, message)
        self.assertIn("nested namespaces are not supported", message)

    def test_sibling_claims_are_fine(self):
        class SiblingConfig(MontrekAppConfig):
            namespace = "other_subtree"

        self.assertEqual(
            declaring_namespace_class(SiblingConfig).namespace, "other_subtree"
        )

    def test_inheriting_a_claim_without_adding_one_is_fine(self):
        class LeafConfig(SubtreeBaseConfig):
            name = "baseclasses"
            default = True

        self.assertIs(declaring_namespace_class(LeafConfig), SubtreeBaseConfig)


class TestFindNamespaceBaseWithIndependentNestedClaims(TestCase):
    """``_raise_for_nested_namespaces`` only sees one hierarchy, so two separate
    configs can still claim ``a`` and ``a.b``. Which one a generated app
    inherits must not depend on app registration order."""

    def setUp(self):
        self.outer = type(
            "OuterConfig", (MontrekAppConfig,), {"namespace": "outer_root"}
        )
        self.inner = type(
            "InnerConfig", (MontrekAppConfig,), {"namespace": "outer_root.area"}
        )

    def _find(self, *order):
        module = apps.get_app_config("baseclasses").module
        installed = [cls(f"{cls.namespace}.app", module) for cls in order]
        with mock.patch.object(apps, "get_app_configs", return_value=installed):
            return find_namespace_base("outer_root.area.new_app")

    def test_the_innermost_claim_wins_whatever_the_order(self):
        self.assertIs(self._find(self.outer, self.inner), self.inner)
        self.assertIs(self._find(self.inner, self.outer), self.inner)

    def test_an_app_outside_the_inner_claim_gets_the_outer_one(self):
        module = apps.get_app_config("baseclasses").module
        installed = [
            cls(f"{cls.namespace}.app", module) for cls in (self.inner, self.outer)
        ]
        with mock.patch.object(apps, "get_app_configs", return_value=installed):
            self.assertIs(find_namespace_base("outer_root.other"), self.outer)

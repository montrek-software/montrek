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
    namespace_claims,
)


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

            class BrokenConfig(MontrekAppConfig):
                name = "baseclasses"

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


# A root subtree, an area inside it, and a single app inside that area with a
# policy of its own.
ROOT_NAMESPACE = "nested_root"
AREA_NAMESPACE = "nested_root.area"
INNER_NAMESPACE = "nested_root.area.inner"


class RootConfig(MontrekAppConfig):
    namespace = ROOT_NAMESPACE
    access_policy = AccessPolicy.RESTRICTED


class AreaConfig(RootConfig):
    namespace = AREA_NAMESPACE


class InnerConfig(AreaConfig):
    namespace = INNER_NAMESPACE


class UnclaimedConfig(MontrekAppConfig):
    pass


class TestIsBelowNamespace(TestCase):
    def test_matches_the_namespace_itself_and_what_is_under_it(self):
        self.assertTrue(is_below_namespace(ROOT_NAMESPACE, ROOT_NAMESPACE))
        self.assertTrue(is_below_namespace(AREA_NAMESPACE, ROOT_NAMESPACE))

    def test_matches_whole_segments_only(self):
        self.assertFalse(is_below_namespace("nested_root_other", ROOT_NAMESPACE))


class TestNamespaceClaims(TestCase):
    """Nested subtrees claim a namespace per level, and every level has to stay
    visible - an outer claim nobody can see is an outer claim nobody enforces."""

    def test_every_level_of_the_hierarchy_is_reported(self):
        self.assertEqual(
            namespace_claims(InnerConfig),
            [
                (INNER_NAMESPACE, InnerConfig),
                (AREA_NAMESPACE, AreaConfig),
                (ROOT_NAMESPACE, RootConfig),
            ],
        )

    def test_attribute_lookup_alone_would_only_see_the_innermost(self):
        """The reason namespace_claims walks the MRO at all."""
        self.assertEqual(InnerConfig.namespace, INNER_NAMESPACE)

    def test_claims_are_most_specific_first(self):
        namespaces = [namespace for namespace, _ in namespace_claims(AreaConfig)]

        self.assertEqual(namespaces, [AREA_NAMESPACE, ROOT_NAMESPACE])

    def test_config_claiming_nothing_has_no_claims(self):
        self.assertEqual(namespace_claims(UnclaimedConfig), [])

    def test_accepts_a_class_as_well_as_an_instance(self):
        """It used to return nothing for a class, silently."""
        self.assertEqual(declaring_namespace_class(InnerConfig).__name__, "InnerConfig")


class TestFindNamespaceBase(TestCase):
    """The generator picks an app's base with this, so it has to land on the
    innermost subtree - the outer base carries the wrong access policy."""

    def _find(self, app_name):
        configs = [
            RootConfig(
                f"{ROOT_NAMESPACE}.plain", apps.get_app_config("baseclasses").module
            ),
            AreaConfig(
                f"{AREA_NAMESPACE}.something", apps.get_app_config("baseclasses").module
            ),
            InnerConfig(INNER_NAMESPACE, apps.get_app_config("baseclasses").module),
        ]
        with mock.patch.object(apps, "get_app_configs", return_value=configs):
            return find_namespace_base(app_name)

    def test_app_in_the_innermost_subtree_gets_the_innermost_base(self):
        self.assertIs(self._find(f"{INNER_NAMESPACE}.new_app"), InnerConfig)

    def test_app_in_the_area_gets_the_area_base(self):
        self.assertIs(self._find(f"{AREA_NAMESPACE}.new_app"), AreaConfig)

    def test_app_directly_under_the_root_gets_the_root_base(self):
        self.assertIs(self._find(f"{ROOT_NAMESPACE}.new_app"), RootConfig)

    def test_app_outside_every_claim_gets_nothing(self):
        self.assertIsNone(self._find("somewhere.else.new_app"))

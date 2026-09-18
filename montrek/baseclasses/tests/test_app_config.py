"""MontrekAppConfig - the base an app declares its access policy on.

The interesting part is the ``default`` flag. Django picks an app's config by
inspecting every AppConfig subclass reachable in its ``apps.py`` and skipping
those with ``default = False``; when that leaves no candidate it silently falls
back to a plain ``AppConfig``. A config inheriting ``default = False`` from this
base would therefore lose its access policy without any warning, so the base
refuses to be subclassed that way.
"""

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from baseclasses.access import AccessKind, AccessPolicy
from baseclasses.app_config import MontrekAppConfig


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

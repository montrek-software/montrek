"""Startup checks guarding the per-app access policy.

Both checks are silent while no app is restricted, which is why each case here
restricts one first. The module doubles as the URLconf for the view checks: the
test views below live in an app (``baseclasses``) whose policy the tests swap
out, and overriding ROOT_URLCONF keeps the walk to exactly these patterns.
"""

from unittest import mock

from django.apps import apps
from django.core.checks import registry
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import include, path
from django.views.decorators.http import require_safe

from baseclasses.access import (
    AccessKind,
    AccessPolicy,
    clear_access_policy_cache,
)
from baseclasses.app_config import MontrekAppConfig
from baseclasses.checks import (
    check_access_policy_declarations,
    check_claimed_namespaces,
    check_restricted_app_views,
)
from baseclasses.views import MontrekDeleteView, MontrekListView

HOST_APP = "baseclasses"


class CheckTestPermission:
    def __init__(self, namespaced_codename: str):
        self.namespaced_codename = namespaced_codename


READ_PERMISSION = CheckTestPermission("baseclasses.can_view")
WRITE_PERMISSION = CheckTestPermission("baseclasses.can_update")


# --- views and URLconf used by the view check tests -------------------------


class GatedListView(MontrekListView):
    """Reachable as long as the app maps AccessKind.VIEW."""


class GatedDeleteView(MontrekDeleteView):
    """Reachable only if the app maps AccessKind.DELETE as well."""


class ExplicitlyGatedListView(MontrekListView):
    permission_required = ["some_app.explicit_permission"]


class OutsideAppListView(MontrekListView):
    """A view class living outside any app - as the classes in a ``utils/`` or
    ``user_groups/`` package do, since those carry no ``apps.py``."""

    __module__ = "some.helper.package"


class OutsideAppExplicitListView(MontrekListView):
    """Same, but carrying its own permission, which is the documented fix."""

    __module__ = "some.helper.package"
    permission_required = ["some_app.explicit_permission"]


@require_safe
def ungated_function_view(request):
    """Carries no permission gate - which is what the check must report.

    ``require_safe`` keeps the fixture read-only all the same: the check walks
    URL patterns, so nothing here needs to answer an unsafe method.
    """
    return HttpResponse("no permission gate at all")


urlpatterns = [
    path("gated-list/", GatedListView.as_view(), name="test_gated_list"),
    path("gated-delete/", GatedDeleteView.as_view(), name="test_gated_delete"),
    path(
        "explicit/",
        ExplicitlyGatedListView.as_view(),
        name="test_explicitly_gated",
    ),
]

FUNCTION_VIEW_URLPATTERNS = urlpatterns + [
    path("ungated/", ungated_function_view, name="test_ungated"),
]

# Views whose class lives outside the app routing them.
OUTSIDE_APP_URLPATTERNS = [
    path("outside/", OutsideAppListView.as_view(), name="test_outside"),
    path(
        "outside-explicit/",
        OutsideAppExplicitListView.as_view(),
        name="test_outside_explicit",
    ),
]

# The routing module of a plain ``include([...])`` is the one of its parent.
NESTED_URLPATTERNS = [
    path("nested/", include(OUTSIDE_APP_URLPATTERNS)),
]


class RestrictedHostAppTestCase(TestCase):
    """Restrict ``HOST_APP`` for the duration of a test."""

    access_permissions: dict = {
        AccessKind.VIEW: READ_PERMISSION,
        AccessKind.DELETE: WRITE_PERMISSION,
    }

    def setUp(self):
        super().setUp()
        self.restrict_host_app(self.access_permissions)

    def restrict_host_app(self, access_permissions):
        app_config = apps.get_app_config(HOST_APP)
        for attribute, value in (
            ("access_policy", AccessPolicy.RESTRICTED),
            ("access_permissions", access_permissions),
        ):
            patch = mock.patch.object(app_config, attribute, value, create=True)
            patch.start()
            self.addCleanup(patch.stop)
        clear_access_policy_cache()
        self.addCleanup(clear_access_policy_cache)


# --- namespace check --------------------------------------------------------


class NamespaceBaseConfig(MontrekAppConfig):
    namespace = "test_subtree"
    access_policy = AccessPolicy.RESTRICTED


class InsideSubtreeConfig(NamespaceBaseConfig):
    pass


class EscapedConfig(MontrekAppConfig):
    pass


class RivalNamespaceConfig(MontrekAppConfig):
    namespace = "test_subtree"


def _app_config(config_class, app_name):
    """An app config instance without going through Django's discovery."""
    return config_class(app_name, apps.get_app_config(HOST_APP).module)


class TestClaimedNamespaces(TestCase):
    def _run_with(self, *app_configs):
        with mock.patch.object(apps, "get_app_configs", return_value=list(app_configs)):
            return check_claimed_namespaces()

    def test_no_claim_means_no_errors(self):
        errors = self._run_with(_app_config(EscapedConfig, "test_subtree.outside"))

        self.assertEqual(errors, [])

    def test_subtree_using_the_base_passes(self):
        errors = self._run_with(
            _app_config(InsideSubtreeConfig, "test_subtree.first"),
            _app_config(InsideSubtreeConfig, "test_subtree.second"),
        )

        self.assertEqual(errors, [])

    def test_app_below_the_namespace_that_escaped_the_base(self):
        errors = self._run_with(
            _app_config(InsideSubtreeConfig, "test_subtree.first"),
            _app_config(EscapedConfig, "test_subtree.escaped"),
        )

        self.assertEqual([error.id for error in errors], ["montrek.E001"])
        self.assertIn("test_subtree.escaped", errors[0].msg)

    def test_app_outside_the_namespace_is_none_of_its_business(self):
        errors = self._run_with(
            _app_config(InsideSubtreeConfig, "test_subtree.first"),
            _app_config(EscapedConfig, "other_subtree.elsewhere"),
        )

        self.assertEqual(errors, [])

    def test_namespace_prefix_must_match_a_full_path_segment(self):
        """``test_subtree_other`` is not below ``test_subtree``."""
        errors = self._run_with(
            _app_config(InsideSubtreeConfig, "test_subtree.first"),
            _app_config(EscapedConfig, "test_subtree_other"),
        )

        self.assertEqual(errors, [])

    def test_one_namespace_claimed_twice_is_still_enforced(self):
        """Not an error in itself - both classes gate the subtree, and the
        first one claiming it wins, as find_namespace_base does."""
        errors = self._run_with(
            _app_config(InsideSubtreeConfig, "test_subtree.first"),
            _app_config(RivalNamespaceConfig, "test_subtree.second"),
        )

        self.assertEqual([error.id for error in errors], ["montrek.E001"])


# --- view check -------------------------------------------------------------


@override_settings(ROOT_URLCONF=__name__)
class TestRestrictedAppViews(RestrictedHostAppTestCase):
    def test_fully_mapped_views_pass(self):
        self.assertEqual(check_restricted_app_views(), [])

    def test_montrek_base_views_expose_their_class_to_the_walk(self):
        """The check reads ``view_class``, which MontrekApiViewMixin's own
        as_view() has to carry over."""
        self.assertIs(GatedListView.as_view().view_class, GatedListView)


@override_settings(ROOT_URLCONF=__name__)
class TestUnmappedAccessKind(RestrictedHostAppTestCase):
    access_permissions = {AccessKind.VIEW: READ_PERMISSION}

    def test_view_whose_access_kind_is_unmapped_is_reported(self):
        # The gate logs the same misconfiguration when it denies at
        # request time; asserted here so the log stays out of the
        # test output.
        with self.assertLogs("baseclasses.access", level="ERROR"):
            errors = check_restricted_app_views()

        self.assertEqual([error.id for error in errors], ["montrek.E004"])
        self.assertIn("GatedDeleteView", errors[0].obj)
        self.assertIn("delete", errors[0].msg)


@override_settings(ROOT_URLCONF=__name__)
class TestExplicitPermissionSatisfiesTheCheck(RestrictedHostAppTestCase):
    access_permissions: dict = {}

    def test_only_the_views_without_their_own_permission_are_reported(self):
        with self.assertLogs("baseclasses.access", level="ERROR"):
            errors = check_restricted_app_views()

        reported = {error.obj for error in errors}
        self.assertNotIn(
            f"{__name__}.ExplicitlyGatedListView",
            reported,
            "a view declaring permission_required needs no app mapping",
        )
        self.assertIn(f"{__name__}.GatedListView", reported)


class TestUngatedFunctionView(RestrictedHostAppTestCase):
    def test_function_based_view_in_a_restricted_app_is_reported(self):
        with (
            override_settings(ROOT_URLCONF=__name__),
            mock.patch(f"{__name__}.urlpatterns", FUNCTION_VIEW_URLPATTERNS),
        ):
            errors = check_restricted_app_views()

        self.assertEqual([error.id for error in errors], ["montrek.E003"])
        self.assertIn("ungated_function_view", errors[0].obj)


class TestViewClassOutsideTheRoutingApp(RestrictedHostAppTestCase):
    """The gate resolves the policy from the view class' module, so a class
    routed from a restricted app but defined outside it is ungated."""

    def _check_with(self, urlpatterns_):
        with (
            override_settings(ROOT_URLCONF=__name__),
            mock.patch(f"{__name__}.urlpatterns", urlpatterns_),
        ):
            return check_restricted_app_views()

    def test_foreign_view_class_is_reported(self):
        errors = self._check_with(OUTSIDE_APP_URLPATTERNS)

        self.assertEqual([error.id for error in errors], ["montrek.E003"])
        self.assertIn("OutsideAppListView", errors[0].obj)
        self.assertIn(__name__, errors[0].msg)

    def test_foreign_view_class_with_its_own_permission_passes(self):
        errors = self._check_with([OUTSIDE_APP_URLPATTERNS[1]])

        self.assertEqual(errors, [])

    def test_routing_module_is_inherited_through_a_plain_include(self):
        errors = self._check_with(NESTED_URLPATTERNS)

        self.assertEqual([error.id for error in errors], ["montrek.E003"])
        self.assertIn("OutsideAppListView", errors[0].obj)


@override_settings(ROOT_URLCONF=__name__)
class TestOpenAppViews(TestCase):
    def setUp(self):
        super().setUp()
        clear_access_policy_cache()
        self.addCleanup(clear_access_policy_cache)

    def test_open_app_reports_nothing(self):
        """Including the ungated function view - that is the old default."""
        with mock.patch(f"{__name__}.urlpatterns", FUNCTION_VIEW_URLPATTERNS):
            self.assertEqual(check_restricted_app_views(), [])

    def test_open_app_routing_a_foreign_view_class_reports_nothing(self):
        with mock.patch(f"{__name__}.urlpatterns", OUTSIDE_APP_URLPATTERNS):
            self.assertEqual(check_restricted_app_views(), [])


class TestChecksAreRegistered(TestCase):
    def test_every_check_runs_at_startup(self):
        registered = set(registry.registry.get_checks())

        self.assertIn(check_access_policy_declarations, registered)
        self.assertIn(check_claimed_namespaces, registered)
        self.assertIn(check_restricted_app_views, registered)


class TestAccessPolicyDeclarations(TestCase):
    """A policy the resolver cannot read has to be reported, not raised: the
    resolver's exception would surface inside the URL walk and abort the run."""

    def setUp(self):
        super().setUp()
        clear_access_policy_cache()
        self.addCleanup(clear_access_policy_cache)

    def _run_with(self, access_policy):
        app_config = type(
            "StubAppConfig", (), {"label": "stub_app", "access_policy": access_policy}
        )()
        with mock.patch.object(apps, "get_app_configs", return_value=[app_config]):
            return check_access_policy_declarations()

    def test_a_valid_policy_passes(self):
        self.assertEqual(self._run_with(AccessPolicy.RESTRICTED), [])

    def test_a_misspelled_policy_is_reported(self):
        errors = self._run_with("restrcted")

        self.assertEqual([error.id for error in errors], ["montrek.E005"])
        self.assertIn("restrcted", errors[0].msg)

    def test_the_url_walk_survives_a_misspelled_policy(self):
        """Otherwise the checks run ends in a traceback and the E005 above is
        never shown."""
        app_config = apps.get_app_config(HOST_APP)
        with mock.patch.object(app_config, "access_policy", "restrcted", create=True):
            clear_access_policy_cache()
            check_restricted_app_views()

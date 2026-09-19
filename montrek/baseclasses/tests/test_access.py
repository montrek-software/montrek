"""Per-app access policy resolution and the gate that consumes it.

The default is unchanged: an app that declares no policy is open, and a view
without ``permission_required`` in such an app lets everybody through. A
restricted app reverses that for its own views only.
"""

from enum import Enum
from unittest import mock

from django.apps import apps
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory
from django.urls import reverse
from django.test import TestCase

from baseclasses import views
from baseclasses.access import (
    UNCONFIGURED_PERMISSION,
    AccessKind,
    AccessPolicy,
    AppAccessPolicy,
    clear_access_policy_cache,
    declared_access_permissions,
    declared_access_policy,
    permissions_for_view,
    resolve_app_policy,
)
from reporting.views import MontrekReportFieldEditView, MontrekReportView

# The app a view is restricted through is resolved from the view class'
# __module__, so the tests borrow a real app rather than inventing a module
# path that belongs to nothing.
HOST_APP = "montrek_example"
HOST_MODULE = "montrek_example.views"


class AccessTestPermissions(Enum):
    """Shaped like the permission enums the apps declare."""

    CAN_VIEW = "Kann Testdaten sehen"
    CAN_CREATE = "Kann Testdaten erstellen"
    CAN_UPDATE = "Kann Testdaten aendern"
    CAN_DELETE = "Kann Testdaten loeschen"

    def __init__(self, permission_name: str):
        self.app_label = "access_test"
        self.permission_name = permission_name
        self.codename = permission_name.lower().replace(" ", "_")
        self.namespaced_codename = f"{self.app_label}.{self.codename}"


FULL_PERMISSIONS = {
    AccessKind.VIEW: AccessTestPermissions.CAN_VIEW,
    AccessKind.CREATE: AccessTestPermissions.CAN_CREATE,
    AccessKind.UPDATE: AccessTestPermissions.CAN_UPDATE,
    AccessKind.DELETE: AccessTestPermissions.CAN_DELETE,
}


class RestrictedAppTestCaseMixin:
    """Turn ``HOST_APP`` into a restricted app for the duration of a test."""

    access_permissions: dict = FULL_PERMISSIONS

    def setUp(self):
        super().setUp()
        app_config = apps.get_app_config(HOST_APP)
        patches = [
            mock.patch.object(
                app_config, "access_policy", AccessPolicy.RESTRICTED, create=True
            ),
            mock.patch.object(
                app_config, "access_permissions", self.access_permissions, create=True
            ),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        clear_access_policy_cache()
        # The cache outlives the patches, so it has to be dropped on the way
        # out as well.
        self.addCleanup(clear_access_policy_cache)


class TestResolveAppPolicy(TestCase):
    def setUp(self):
        super().setUp()
        clear_access_policy_cache()
        self.addCleanup(clear_access_policy_cache)

    def test_app_without_declaration_is_open(self):
        policy = resolve_app_policy(HOST_MODULE)

        self.assertFalse(policy.is_restricted)
        self.assertEqual(policy.permissions_for(AccessKind.VIEW), ())

    def test_module_outside_any_app_is_open(self):
        policy = resolve_app_policy("some.package.that.is.no.app")

        self.assertFalse(policy.is_restricted)

    def test_baseclasses_view_module_is_open(self):
        """The shared bases themselves must never carry a policy."""
        self.assertFalse(resolve_app_policy("baseclasses.views").is_restricted)


class TestRestrictedAppPolicy(RestrictedAppTestCaseMixin, TestCase):
    def test_policy_is_restricted(self):
        self.assertTrue(resolve_app_policy(HOST_MODULE).is_restricted)

    def test_each_access_kind_maps_to_its_permission(self):
        for access_kind, permission in FULL_PERMISSIONS.items():
            with self.subTest(access_kind=access_kind):
                self.assertEqual(
                    permissions_for_view(HOST_MODULE, access_kind),
                    (permission.namespaced_codename,),
                )

    def test_other_apps_stay_open(self):
        self.assertEqual(permissions_for_view("baseclasses.views", AccessKind.VIEW), ())


class TestUnconfiguredAccessKind(RestrictedAppTestCaseMixin, TestCase):
    access_permissions = {AccessKind.VIEW: AccessTestPermissions.CAN_VIEW}

    def test_missing_access_kind_denies_instead_of_allowing(self):
        with self.assertLogs("baseclasses.access", level="ERROR"):
            permissions = permissions_for_view(HOST_MODULE, AccessKind.DELETE)

        self.assertEqual(permissions, (UNCONFIGURED_PERMISSION,))

    def test_unconfigured_permission_is_unobtainable(self):
        """Nothing creates it, so has_perms can never satisfy it."""
        from django.contrib.auth.models import Permission

        app_label, codename = UNCONFIGURED_PERMISSION.split(".", 1)
        self.assertFalse(
            Permission.objects.filter(
                content_type__app_label=app_label, codename=codename
            ).exists()
        )


class TestDeclaredAccessPolicy(TestCase):
    """An unusable access_policy must never be read as the permissive one."""

    def _app_config(self, access_policy):
        return type(
            "StubAppConfig", (), {"label": "stub_app", "access_policy": access_policy}
        )()

    def test_enum_member_is_returned_unchanged(self):
        for policy in AccessPolicy:
            with self.subTest(policy=policy):
                self.assertIs(declared_access_policy(self._app_config(policy)), policy)

    def test_app_config_without_a_policy_is_open(self):
        self.assertIs(declared_access_policy(object()), AccessPolicy.OPEN)

    def test_matching_string_is_accepted(self):
        """'restricted' is the obvious thing to write, so it works."""
        self.assertIs(
            declared_access_policy(self._app_config("restricted")),
            AccessPolicy.RESTRICTED,
        )

    def test_typo_raises_instead_of_opening_the_app(self):
        with self.assertRaises(ImproperlyConfigured) as ctx:
            declared_access_policy(self._app_config("restrcted"))

        self.assertIn("restrcted", str(ctx.exception))
        self.assertIn("stub_app", str(ctx.exception))

    def test_non_string_value_raises(self):
        with self.assertRaises(ImproperlyConfigured):
            declared_access_policy(self._app_config(True))


class TestPolicyTypoDoesNotDisableTheGate(TestCase):
    def setUp(self):
        super().setUp()
        clear_access_policy_cache()
        self.addCleanup(clear_access_policy_cache)

    def test_resolver_refuses_a_misspelled_policy(self):
        app_config = apps.get_app_config(HOST_APP)
        with (
            mock.patch.object(app_config, "access_policy", "restrcted", create=True),
            self.assertRaises(ImproperlyConfigured),
        ):
            resolve_app_policy(HOST_MODULE)


class GateTestView(views.MontrekPermissionRequiredMixin):
    """Stands in for a concrete view; ``__module__`` is what gets resolved."""

    __module__ = HOST_MODULE


class TestPermissionGate(RestrictedAppTestCaseMixin, TestCase):
    def _view(self, access_kind=AccessKind.VIEW, permission_required=None):
        view = GateTestView()
        view.access_kind = access_kind
        if permission_required is not None:
            view.permission_required = permission_required
        return view

    def test_explicit_permission_required_wins(self):
        view = self._view(permission_required=["other_app.some_permission"])

        self.assertEqual(view.get_permission_required(), ("other_app.some_permission",))

    def test_falls_back_to_the_app_permission(self):
        view = self._view(access_kind=AccessKind.UPDATE)

        self.assertEqual(
            view.get_permission_required(),
            (AccessTestPermissions.CAN_UPDATE.namespaced_codename,),
        )


class TestOpenAppGate(TestCase):
    def setUp(self):
        super().setUp()
        clear_access_policy_cache()
        self.addCleanup(clear_access_policy_cache)

    def test_view_in_open_app_requires_nothing(self):
        view = GateTestView()

        self.assertEqual(view.get_permission_required(), ())


class TestBaseViewAccessKinds(TestCase):
    """The access kind decides which permission a restricted app demands, so
    the mapping is pinned down here rather than left to the class bodies."""

    EXPECTED = {
        views.MontrekListView: AccessKind.VIEW,
        views.MontrekTemplateView: AccessKind.VIEW,
        views.MontrekHistoryListView: AccessKind.VIEW,
        views.MontrekDetailView: AccessKind.VIEW,
        views.MontrekDownloadView: AccessKind.VIEW,
        views.MontrekRestApiView: AccessKind.VIEW,
        MontrekReportView: AccessKind.VIEW,
        views.MontrekCreateView: AccessKind.CREATE,
        views.MontrekCreateUpdateView: AccessKind.UPDATE,
        views.MontrekUpdateView: AccessKind.UPDATE,
        views.MontrekInlineFieldEditView: AccessKind.UPDATE,
        views.MontrekRedirectView: AccessKind.UPDATE,
        views.MontrekPostActionView: AccessKind.UPDATE,
        views.MontrekHtmxRowActionView: AccessKind.UPDATE,
        MontrekReportFieldEditView: AccessKind.UPDATE,
        views.MontrekDeleteView: AccessKind.DELETE,
    }

    def test_access_kinds(self):
        for view_class, access_kind in self.EXPECTED.items():
            with self.subTest(view=view_class.__name__):
                self.assertIs(view_class.access_kind, access_kind)

    def test_every_base_view_carries_the_gate(self):
        for view_class in self.EXPECTED:
            with self.subTest(view=view_class.__name__):
                self.assertTrue(issubclass(view_class, PermissionRequiredMixin))

    def test_create_update_base_defaults_to_a_write_permission(self):
        """A subclass of the shared create/update base that declares no kind
        must not fall back to the read permission."""
        self.assertIs(views.MontrekCreateUpdateView.access_kind, AccessKind.UPDATE)

    def test_redirect_base_defaults_to_a_write_permission(self):
        """Subclasses change state inside get_redirect_url, so the base cannot
        fall back to the read permission either."""
        self.assertIs(views.MontrekRedirectView.access_kind, AccessKind.UPDATE)


class TestSimpleFileUploadPermission(RestrictedAppTestCaseMixin, TestCase):
    def _list_view(self, simple_file_upload_permission=None):
        view = views.MontrekListView()
        view.__class__ = type(
            "UploadListView",
            (views.MontrekListView,),
            {"__module__": HOST_MODULE},
        )
        if simple_file_upload_permission is not None:
            view.simple_file_upload_permission = simple_file_upload_permission
        return view

    def test_explicit_upload_permission_wins(self):
        view = self._list_view(simple_file_upload_permission=["app.upload"])

        self.assertEqual(view.get_simple_file_upload_permission(), ("app.upload",))

    def test_upload_falls_back_to_create_not_view(self):
        """The list view itself only reads; the upload on it writes."""
        view = self._list_view()

        self.assertEqual(
            view.get_simple_file_upload_permission(),
            (AccessTestPermissions.CAN_CREATE.namespaced_codename,),
        )


class TestOpenAppFileUpload(TestCase):
    def setUp(self):
        super().setUp()
        clear_access_policy_cache()
        self.addCleanup(clear_access_policy_cache)

    def test_upload_in_open_app_requires_nothing(self):
        view = views.MontrekListView()

        self.assertEqual(view.get_simple_file_upload_permission(), ())


class TestAppAccessPolicyDefaults(TestCase):
    def test_default_policy_is_open(self):
        self.assertFalse(AppAccessPolicy().is_restricted)

    def test_open_policy_ignores_configured_permissions(self):
        policy = AppAccessPolicy(policy=AccessPolicy.OPEN, permissions=FULL_PERMISSIONS)

        self.assertEqual(policy.permissions_for(AccessKind.DELETE), ())


class TestMalformedPermissionsDenyRatherThanRaise(TestCase):
    """A misconfigured app must close the gate, not raise.

    Raising would reach the user as a 500, and - worse - would abort the startup
    checks part way through, since they resolve permissions through the same
    code to report the misconfiguration.
    """

    def _app_config(self, access_permissions):
        return type(
            "StubAppConfig",
            (),
            {"label": "stub_app", "access_permissions": access_permissions},
        )()

    def _policy(self, access_permissions):
        return AppAccessPolicy(
            policy=AccessPolicy.RESTRICTED,
            permissions=declared_access_permissions(
                self._app_config(access_permissions)
            ),
            app_label="stub_app",
        )

    def test_permissions_that_cannot_become_a_mapping_deny(self):
        for description, declared in (
            ("a list of non-pairs", [object()]),
            ("a string", "restricted"),
            ("an integer", 7),
        ):
            with self.subTest(description):
                with self.assertLogs("baseclasses.access", level="ERROR"):
                    policy = self._policy(declared)
                    permissions = policy.permissions_for(AccessKind.VIEW)

                self.assertEqual(permissions, (UNCONFIGURED_PERMISSION,))

    def test_a_mapping_given_as_pairs_is_accepted(self):
        policy = self._policy([(AccessKind.VIEW, AccessTestPermissions.CAN_VIEW)])

        self.assertEqual(
            policy.permissions_for(AccessKind.VIEW),
            (AccessTestPermissions.CAN_VIEW.namespaced_codename,),
        )

    def test_permission_without_a_namespaced_codename_denies(self):
        policy = self._policy({AccessKind.VIEW: object()})

        with self.assertLogs("baseclasses.access", level="ERROR"):
            permissions = policy.permissions_for(AccessKind.VIEW)

        self.assertEqual(permissions, (UNCONFIGURED_PERMISSION,))

    def test_permission_with_an_empty_codename_denies(self):
        blank = type("Blank", (), {"namespaced_codename": ""})()
        policy = self._policy({AccessKind.VIEW: blank})

        with self.assertLogs("baseclasses.access", level="ERROR"):
            permissions = policy.permissions_for(AccessKind.VIEW)

        self.assertEqual(permissions, (UNCONFIGURED_PERMISSION,))


class TestStartupChecksSurviveAMalformedApp(RestrictedAppTestCaseMixin, TestCase):
    """The checks must report a malformed app, not die on it."""

    access_permissions = [object()]

    def test_view_check_reports_instead_of_raising(self):
        from baseclasses.checks import check_restricted_app_views

        with self.assertLogs("baseclasses.access", level="ERROR"):
            errors = check_restricted_app_views()

        # The gated views resolve to the unobtainable permission, which is what
        # E004 reports. That the call returned at all is the point: before the
        # resolver was made to fail closed it raised here.
        self.assertIn("montrek.E004", {error.id for error in errors})


class TestNavigationRedirectView(TestCase):
    """The navigational redirect reads; MontrekRedirectView writes."""

    def test_it_is_a_read(self):
        self.assertIs(views.MontrekNavigationRedirectView.access_kind, AccessKind.VIEW)

    def test_it_does_not_inherit_the_write_redirect_base(self):
        """Inheriting MontrekRedirectView would bring its UPDATE kind and its
        get_redirect_url, which raises."""
        self.assertFalse(
            issubclass(views.MontrekNavigationRedirectView, views.MontrekRedirectView)
        )

    def test_it_carries_the_permission_gate(self):
        self.assertTrue(
            issubclass(
                views.MontrekNavigationRedirectView,
                views.MontrekPermissionRequiredMixin,
            )
        )

    def test_as_view_accepts_the_configuration_the_urlconf_passes(self):
        for key in ("pattern_name", "url", "pattern_kwargs"):
            with self.subTest(key):
                self.assertTrue(hasattr(views.MontrekNavigationRedirectView, key))

    def _view(self, **attributes):
        view = views.MontrekNavigationRedirectView()
        # RedirectView reads the query string off the request, so one is needed
        # even for a redirect that ignores it.
        view.request = RequestFactory().get("/")
        for key, value in attributes.items():
            setattr(view, key, value)
        return view

    def test_fixed_kwargs_are_reversed_into_the_target(self):
        docs_name = "01_montrek_software_architecture"
        view = self._view(
            pattern_name="montrek_docs", pattern_kwargs={"docs_name": docs_name}
        )

        self.assertEqual(
            view.get_redirect_url(),
            reverse("montrek_docs", kwargs={"docs_name": docs_name}),
        )

    def test_without_fixed_kwargs_it_behaves_like_redirect_view(self):
        view = self._view(pattern_name="home")

        self.assertEqual(view.get_redirect_url(), reverse("home"))

    def test_a_plain_url_is_passed_through_unchanged(self):
        """Some entry URLs redirect to a path rather than a reversed name."""
        view = self._view(url="somewhere/else")

        self.assertEqual(view.get_redirect_url(), "somewhere/else")

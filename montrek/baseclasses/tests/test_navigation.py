"""The access-aware navigation structure behind the navbar and the launchpad.

The menu shows an entry only to a user who would get past the gate of the view
it routes to, so the permission is resolved from the route rather than declared
alongside the entry. The module doubles as the URLconf: its views live in an app
(``baseclasses``) whose policy the tests swap out, and overriding ROOT_URLCONF
keeps the resolution to exactly these patterns.

Hiding is cosmetic - what the gate does with a request is covered by
``test_access``.
"""

from enum import Enum
from unittest import mock

from django.apps import apps
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.test import SimpleTestCase, override_settings
from django.urls import path

from baseclasses.access import (
    UNCONFIGURED_PERMISSION,
    AccessKind,
    AccessPolicy,
    can_access_url_name,
    clear_access_policy_cache,
    permissions_for_callback,
    permissions_for_url_name,
    route_for_url_name,
)
from baseclasses.navigation import build_nav_structure, navigation_url_names
from baseclasses.views import MontrekListView, MontrekNavigationRedirectView

HOST_APP = "baseclasses"


class NavigationTestPermissions(Enum):
    """Shaped like the permission enums the apps declare."""

    CAN_VIEW = "Kann Testdaten sehen"

    def __init__(self, permission_name: str):
        self.app_label = "navigation_test"
        self.permission_name = permission_name
        self.codename = permission_name.lower().replace(" ", "_")
        self.namespaced_codename = f"{self.app_label}.{self.codename}"


VIEW_PERMISSION = NavigationTestPermissions.CAN_VIEW.namespaced_codename


# --- views and URLconf ------------------------------------------------------


class GatedEntryView(MontrekListView):
    """Behind the app policy, like every entry point of a restricted app."""


class ExplicitlyGatedEntryView(MontrekListView):
    permission_required = ["other_app.some_permission"]


class OpenEntryView(MontrekListView):
    """Outside any app, so no policy applies and everybody may follow it."""

    __module__ = "some.helper.package"


urlpatterns = [
    path("kvg/", GatedEntryView.as_view(), name="kvg"),
    path("fund/", GatedEntryView.as_view(), name="fund"),
    path("datev/", ExplicitlyGatedEntryView.as_view(), name="datev_transaction"),
    path("info/", OpenEntryView.as_view(), name="info"),
    path(
        "menu/",
        MontrekNavigationRedirectView.as_view(
            access_module=__name__, pattern_name="fund"
        ),
        name="menu",
    ),
    path("needs-an-argument/<int:pk>/", GatedEntryView.as_view(), name="detail"),
]


class StubUser:
    """Only ``has_perms`` is reached, and modelling it beats a database row: the
    permissions here belong to no app and would need a content type invented for
    them."""

    def __init__(self, *permissions: str):
        self.permissions = set(permissions)

    def has_perms(self, permissions) -> bool:
        return all(permission in self.permissions for permission in permissions)


class StubSuperuser(StubUser):
    """A superuser holds every permission, which Django answers without looking
    any of them up."""

    def has_perms(self, permissions) -> bool:
        return True


@override_settings(ROOT_URLCONF=__name__)
class NavigationTestCase(SimpleTestCase):
    """Restrict ``HOST_APP`` and route only the patterns above."""

    def setUp(self):
        super().setUp()
        app_config = apps.get_app_config(HOST_APP)
        for attribute, value in (
            ("access_policy", AccessPolicy.RESTRICTED),
            (
                "access_permissions",
                {AccessKind.VIEW: NavigationTestPermissions.CAN_VIEW},
            ),
        ):
            patch = mock.patch.object(app_config, attribute, value, create=True)
            patch.start()
            self.addCleanup(patch.stop)
        # Both the policy and the routes are cached, and the caches outlive the
        # patches and the URLconf override.
        clear_access_policy_cache()
        self.addCleanup(clear_access_policy_cache)


# --- resolving a URL name ---------------------------------------------------


class TestRouteForUrlName(NavigationTestCase):
    def test_a_routed_name_yields_its_url_and_callback(self):
        url, callback = route_for_url_name("fund")

        self.assertEqual(url, "/fund/")
        self.assertIs(callback.view_class, GatedEntryView)

    def test_an_unknown_name_is_none(self):
        self.assertIsNone(route_for_url_name("no_such_entry"))

    def test_a_name_needing_arguments_is_none(self):
        """A menu entry cannot supply them, so the route is unusable here."""
        self.assertIsNone(route_for_url_name("detail"))


class TestPermissionsForUrlName(NavigationTestCase):
    def test_the_app_policy_applies_to_a_gated_entry(self):
        self.assertEqual(permissions_for_url_name("fund"), (VIEW_PERMISSION,))

    def test_an_explicit_permission_wins(self):
        self.assertEqual(
            permissions_for_url_name("datev_transaction"),
            ("other_app.some_permission",),
        )

    def test_a_redirect_entry_resolves_through_its_access_module(self):
        """The class lives in ``baseclasses``; ``access_module`` is what ties it
        to the app the URL belongs to."""
        self.assertEqual(permissions_for_url_name("menu"), (VIEW_PERMISSION,))

    def test_an_open_entry_requires_nothing(self):
        self.assertEqual(permissions_for_url_name("info"), ())

    def test_an_unroutable_name_requires_a_permission_nobody_holds(self):
        self.assertEqual(
            permissions_for_url_name("no_such_entry"), (UNCONFIGURED_PERMISSION,)
        )


class TestCanAccessUrlName(NavigationTestCase):
    def test_the_permission_holder_may(self):
        self.assertTrue(can_access_url_name(StubUser(VIEW_PERMISSION), "fund"))

    def test_without_the_permission_may_not(self):
        self.assertFalse(can_access_url_name(StubUser(), "fund"))

    def test_an_open_entry_is_open_to_everybody(self):
        self.assertTrue(can_access_url_name(StubUser(), "info"))
        self.assertTrue(can_access_url_name(AnonymousUser(), "info"))

    def test_an_unroutable_entry_is_hidden_from_a_superuser_too(self):
        """A superuser passes every permission check, so routability has to be
        asked separately - otherwise the one user who sees everything is handed
        a link that cannot be reversed."""
        self.assertFalse(can_access_url_name(StubSuperuser(), "no_such_entry"))


class TestRouteResolutionAgreesWithTheGate(NavigationTestCase):
    """``as_view`` accepts any declared class attribute, so a route may override
    what the gate reads. Resolving a route has to follow every one of those, or
    the menu shows an entry for a permission the gate does not ask for."""

    def _gate_permissions(self, callback) -> tuple[str, ...]:
        """What the view itself would demand, built the way ``as_view`` does."""
        view = callback.view_class(**callback.view_initkwargs)
        return view.get_permission_required()

    def _assert_agree(self, callback):
        self.assertEqual(
            permissions_for_callback(callback), self._gate_permissions(callback)
        )

    def test_a_plain_route(self):
        self._assert_agree(GatedEntryView.as_view())

    def test_a_route_naming_its_access_kind(self):
        self._assert_agree(GatedEntryView.as_view(access_kind=AccessKind.DELETE))

    def test_a_route_naming_its_permission(self):
        self._assert_agree(
            GatedEntryView.as_view(permission_required=["app.some_permission"])
        )

    def test_a_route_clearing_the_class_permission(self):
        self._assert_agree(ExplicitlyGatedEntryView.as_view(permission_required=[]))

    def test_a_route_naming_its_access_module(self):
        self._assert_agree(
            MontrekNavigationRedirectView.as_view(
                access_module=__name__, pattern_name="fund"
            )
        )


# --- the structure the templates render -------------------------------------


@override_settings(
    NAVBAR_APPS=[
        "asset_management.kvg",
        "asset_management.fund",
        "risk_management.menu",
        "datev_transaction",
        "info",
    ],
    NAVBAR_RENAME={"asset_management": "Verwaltung", "fund": "Fonds"},
)
class TestBuildNavStructure(NavigationTestCase):
    @staticmethod
    def _names(user) -> tuple[list[str], dict[str, list[str]]]:
        navbar_apps, navbar_dropdowns = build_nav_structure(user)
        return (
            [app.app_name for app in navbar_apps],
            {
                dropdown.dropdown_name: [
                    item.app_name for item in dropdown.dropdown_items
                ]
                for dropdown in navbar_dropdowns
            },
        )

    def test_a_user_without_permissions_keeps_only_the_open_entry(self):
        apps_, dropdowns = self._names(StubUser())

        self.assertEqual(apps_, ["info"])
        self.assertEqual(dropdowns, {})

    def test_the_permission_holder_sees_the_gated_entries(self):
        apps_, dropdowns = self._names(StubUser(VIEW_PERMISSION))

        self.assertEqual(apps_, ["info"])
        self.assertEqual(
            dropdowns,
            {"asset_management": ["kvg", "fund"], "risk_management": ["menu"]},
        )

    def test_a_dropdown_without_an_accessible_item_does_not_appear(self):
        """It is dropped rather than rendered as an empty menu."""
        _, dropdowns = self._names(StubUser("other_app.some_permission"))

        self.assertEqual(dropdowns, {})

    def test_an_explicitly_gated_entry_follows_its_own_permission(self):
        apps_, _ = self._names(StubUser("other_app.some_permission"))

        self.assertEqual(apps_, ["datev_transaction", "info"])

    def test_entries_keep_the_configured_order(self):
        _, dropdowns = self._names(StubUser(VIEW_PERMISSION))

        self.assertEqual(dropdowns["asset_management"], ["kvg", "fund"])

    def test_an_entry_carries_its_url(self):
        _, navbar_dropdowns = build_nav_structure(StubUser(VIEW_PERMISSION))
        urls = {
            item.app_name: item.url
            for dropdown in navbar_dropdowns
            for item in dropdown.dropdown_items
        }

        self.assertEqual(urls["fund"], "/fund/")
        self.assertEqual(urls["menu"], "/menu/")

    def test_the_rename_configuration_still_applies(self):
        _, navbar_dropdowns = build_nav_structure(StubUser(VIEW_PERMISSION))
        dropdown = navbar_dropdowns[0]

        self.assertEqual(dropdown.display_name, "Verwaltung")
        self.assertEqual(dropdown.dropdown_items[1].display_name, "Fonds")

    @override_settings(NAVBAR_APPS=["asset_management.no_such_entry"])
    def test_an_unroutable_entry_is_dropped(self):
        apps_, dropdowns = self._names(StubSuperuser())

        self.assertEqual(apps_, [])
        self.assertEqual(dropdowns, {})

    @override_settings(NAVBAR_APPS=["", "info"])
    def test_an_empty_entry_is_ignored(self):
        """``NAVBAR_APPS`` is split out of a string, so an unset setting arrives
        as one empty entry."""
        apps_, _ = self._names(StubUser())

        self.assertEqual(apps_, ["info"])


@override_settings(NAVBAR_APPS=["asset_management.fund", "info"])
class TestNavigationUrlNames(NavigationTestCase):
    def test_the_last_segment_is_the_url_name(self):
        self.assertEqual(navigation_url_names(), ["fund", "info"])


# --- what the launchpad renders ---------------------------------------------


@override_settings(NAVBAR_APPS=["asset_management.fund", "info"])
class TestLaunchpadTemplate(NavigationTestCase):
    """The navbar is not rendered here: it reverses the login and account URLs,
    which this URLconf does not route."""

    @staticmethod
    def _render(user) -> str:
        return Template("{% load base_tags %}{% include_launchpad %}").render(
            Context({"user": user})
        )

    def test_a_gated_card_is_hidden_without_the_permission(self):
        html = self._render(StubUser())

        self.assertNotIn('href="/fund/"', html)
        self.assertIn('href="/info/"', html)

    def test_a_gated_card_is_shown_to_the_permission_holder(self):
        html = self._render(StubUser(VIEW_PERMISSION))

        self.assertIn('href="/fund/"', html)

    @override_settings(NAVBAR_APPS=["asset_management.fund"])
    def test_a_user_with_nothing_gets_an_empty_state(self):
        html = self._render(StubUser())

        self.assertNotIn("launchpad-card", html)
        self.assertIn("empty-state", html)

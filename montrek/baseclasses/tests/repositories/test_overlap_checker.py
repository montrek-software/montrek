from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from baseclasses import models as bc_models
from baseclasses.repositories.db.overlap_checker import (
    OverlapFinding,
    find_overlapping_versions,
)
from baseclasses.tests.factories.baseclass_factories import (
    LinkTestMontrekTestLinkFactory,
    TestHubValueDateFactory,
    TestMontrekSatelliteFactory,
    TestMontrekTimeSeriesSatelliteFactory,
)
from baseclasses.utils import montrek_time


class TestFindOverlappingVersions(TestCase):
    def test_no_findings_for_consecutive_versions(self):
        first = TestMontrekSatelliteFactory(
            state_date_start=montrek_time(2023, 1, 1),
            state_date_end=montrek_time(2023, 6, 1),
        )
        # Validity is half-open, so a version starting where the previous one
        # ends does not overlap it.
        TestMontrekSatelliteFactory(
            hub_entity=first.hub_entity,
            state_date_start=montrek_time(2023, 6, 1),
        )

        self.assertEqual(find_overlapping_versions(), [])

    def test_overlapping_satellite_versions_are_found(self):
        first = TestMontrekSatelliteFactory(
            state_date_start=montrek_time(2023, 1, 1),
            state_date_end=montrek_time(2023, 6, 1),
        )
        TestMontrekSatelliteFactory(
            hub_entity=first.hub_entity,
            state_date_start=montrek_time(2023, 3, 1),
        )
        TestMontrekSatelliteFactory()

        self.assertEqual(
            find_overlapping_versions(),
            [
                OverlapFinding(
                    model=bc_models.TestMontrekSatellite,
                    key_field="hub_entity",
                    key_values=[first.hub_entity_id],
                )
            ],
        )

    def test_overlapping_timeseries_versions_are_found(self):
        hub_value_date = TestHubValueDateFactory()
        TestMontrekTimeSeriesSatelliteFactory(hub_value_date=hub_value_date)
        TestMontrekTimeSeriesSatelliteFactory(hub_value_date=hub_value_date)

        findings = find_overlapping_versions()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].model, bc_models.TestMontrekTimeSeriesSatellite)
        self.assertEqual(findings[0].key_field, "hub_value_date")
        self.assertEqual(findings[0].key_values, [hub_value_date.pk])

    def test_concurrent_one_to_one_links_are_found_per_side(self):
        link = LinkTestMontrekTestLinkFactory()
        LinkTestMontrekTestLinkFactory(hub_in=link.hub_in)

        findings = find_overlapping_versions()

        self.assertEqual(
            findings,
            [
                OverlapFinding(
                    model=bc_models.LinkTestMontrekTestLink,
                    key_field="hub_in",
                    key_values=[link.hub_in_id],
                )
            ],
        )


class TestCheckOverlappingVersionsCommand(TestCase):
    def test_reports_success_without_overlaps(self):
        out = StringIO()

        call_command("check_overlapping_versions", stdout=out)

        self.assertIn("No overlapping versions", out.getvalue())

    def test_fails_for_unknown_app_label(self):
        with self.assertRaisesMessage(CommandError, "Unknown app label: basclasses"):
            call_command("check_overlapping_versions", "basclasses", stdout=StringIO())

    def test_fails_with_overlaps(self):
        first = TestMontrekSatelliteFactory()
        TestMontrekSatelliteFactory(hub_entity=first.hub_entity)
        out = StringIO()

        with self.assertRaises(CommandError):
            call_command("check_overlapping_versions", stdout=out)

        self.assertIn("baseclasses.TestMontrekSatellite", out.getvalue())
        self.assertIn(str(first.hub_entity_id), out.getvalue())

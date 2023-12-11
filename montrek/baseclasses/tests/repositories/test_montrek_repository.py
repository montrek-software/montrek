from django.test import TestCase
from django.utils import timezone
from baseclasses.utils import montrek_time
from baseclasses.tests.factories.baseclass_factories import TestMontrekSatelliteFactory
from baseclasses.tests.factories.baseclass_factories import TestLinkSatelliteFactory
from baseclasses.models import TestMontrekHub
from baseclasses.models import TestMontrekSatellite
from baseclasses.models import TestLinkHub
from baseclasses.models import TestLinkSatellite
from baseclasses.repositories.montrek_repository import MontrekRepository


class DummyMontrekRepository(MontrekRepository):
    hub_class = TestMontrekHub


class TestMontrekRepository(TestCase):
    def setUp(self):
        self.test_sat_1 = TestMontrekSatelliteFactory.create()
        self.test_sat_2 = TestMontrekSatelliteFactory.create(
            hub_entity=self.test_sat_1.hub_entity,
            state_date_start=self.test_sat_1.state_date_end,
            state_date_end=timezone.datetime.max,
            test_name="test_sat_2",
            test_value=2,
        )
        self.test_linkes_sat_1 = TestLinkSatelliteFactory.create()
        self.test_linkes_sat_2 = TestLinkSatelliteFactory.create(
            hub_entity=self.test_linkes_sat_1.hub_entity,
            state_date_start=self.test_linkes_sat_1.state_date_end,
            state_date_end=timezone.datetime.max,
        )
        self.test_linkes_sat_1.hub_entity.link_link_hub_test_montrek_hub.add(
            self.test_sat_1.hub_entity
        )

    def tearDown(self):
        TestMontrekSatellite.objects.all().delete()
        TestMontrekHub.objects.all().delete()
        TestLinkSatellite.objects.all().delete()
        TestLinkHub.objects.all().delete()

    def test_build_queryset_with_satellite_fields(self):
        test_montrek_repository = DummyMontrekRepository(None)
        test_montrek_repository.add_satellite_fields_annotations(
            TestMontrekSatellite, ["test_name", "test_value"], montrek_time(2023, 6, 30)
        )
        test_queryset = test_montrek_repository.build_queryset()
        self.assertEqual(test_queryset.count(), 1)
        self.assertEqual(test_queryset.first().test_name, self.test_sat_1.test_name)
        self.assertEqual(test_queryset.first().test_value, self.test_sat_1.test_value)

        test_montrek_repository = DummyMontrekRepository(None)
        test_montrek_repository.add_satellite_fields_annotations(
            TestMontrekSatellite, ["test_name", "test_value"], montrek_time(2023, 8, 30)
        )
        test_queryset = test_montrek_repository.build_queryset()
        self.assertEqual(test_queryset.count(), 1)
        self.assertEqual(test_queryset.first().test_name, "test_sat_2")
        self.assertEqual(test_queryset.first().test_value, "2")

        test_montrek_repository = DummyMontrekRepository(None)
        test_montrek_repository.add_satellite_fields_annotations(
            TestMontrekSatellite, ["test_name", "test_value"], montrek_time(2022, 8, 30)
        )
        test_queryset = test_montrek_repository.build_queryset()
        self.assertEqual(test_queryset.count(), 1)
        self.assertIsNone(test_queryset.first().test_name)
        self.assertIsNone(test_queryset.first().test_value)

    def test_build_queryset_with_linked_satellite_fields(self):
        test_montrek_repository = DummyMontrekRepository(None)
        test_montrek_repository.add_linked_satellites_field_annotations(
            TestLinkSatellite,
            "link_test_montrek_hub_link_hub__testlinksatellite",
            ["test_id"],
            montrek_time(2023, 6, 30),
        )
        test_queryset = test_montrek_repository.build_queryset()
        self.assertEqual(test_queryset.count(), 2)
        self.assertEqual(
            test_queryset.first().testlinksatellite__test_id,
            self.test_linkes_sat_1.test_id,
        )
        test_montrek_repository = DummyMontrekRepository(None)
        test_montrek_repository.add_linked_satellites_field_annotations(
            TestLinkSatellite,
            "link_test_montrek_hub_link_hub__testlinksatellite",
            ["test_id"],
            montrek_time(2023, 8, 30),
        )
        test_queryset = test_montrek_repository.build_queryset()
        self.assertEqual(test_queryset.count(), 2)
        self.assertEqual(
            test_queryset.first().testlinksatellite__test_id,
            self.test_linkes_sat_2.test_id,
        )

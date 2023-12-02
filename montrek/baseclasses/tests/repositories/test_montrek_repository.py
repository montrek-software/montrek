from django.test import TestCase
from django.utils import timezone
from baseclasses.utils import montrek_time
from baseclasses.tests.factories.baseclass_factories import TestMontrekSatelliteFactory
from baseclasses.models import TestMontrekHub
from baseclasses.models import TestMontrekSatellite
from baseclasses.repositories.montrek_repository import MontrekRepository


class TestMontrekRepository(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_sat_1 = TestMontrekSatelliteFactory.create()
        cls.test_sat_2 = TestMontrekSatelliteFactory.create(
            hub_entity=cls.test_sat_1.hub_entity,
            state_date_start=cls.test_sat_1.state_date_end,
            state_date_end=timezone.datetime.max,
            test_name="test_sat_2",
            test_value=2
        )

    def test_build_queryset_with_satellite_fields(self):
        test_montrek_repository = MontrekRepository(TestMontrekHub)
        test_montrek_repository.add_satellite_fields_annotations(
            TestMontrekSatellite, ["test_name", "test_value"], montrek_time(2023, 6, 30)
        )
        test_queryset = test_montrek_repository.build_queryset()
        self.assertEqual(test_queryset.count(), 1)
        self.assertEqual(test_queryset.first().test_name, self.test_sat_1.test_name)
        self.assertEqual(test_queryset.first().test_value, self.test_sat_1.test_value)

        test_montrek_repository = MontrekRepository(TestMontrekHub)
        test_montrek_repository.add_satellite_fields_annotations(
            TestMontrekSatellite, ["test_name", "test_value"], montrek_time(2023, 8, 30)
        )
        test_queryset = test_montrek_repository.build_queryset()
        self.assertEqual(test_queryset.count(), 1)
        self.assertEqual(test_queryset.first().test_name, 'test_sat_2')
        self.assertEqual(test_queryset.first().test_value, '2')

        test_montrek_repository = MontrekRepository(TestMontrekHub)
        test_montrek_repository.add_satellite_fields_annotations(
            TestMontrekSatellite, ["test_name", "test_value"], montrek_time(2022, 8, 30)
        )
        test_queryset = test_montrek_repository.build_queryset()
        self.assertEqual(test_queryset.count(), 1)
        self.assertIsNone(test_queryset.first().test_name)
        self.assertIsNone(test_queryset.first().test_value)

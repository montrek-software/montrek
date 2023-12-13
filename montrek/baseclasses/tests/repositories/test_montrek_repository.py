from django.test import TestCase
from django.utils import timezone
from baseclasses.utils import montrek_time
from baseclasses.tests.factories import baseclass_factories as bc_factories
from baseclasses import models as bc_models
from baseclasses.repositories.montrek_repository import MontrekRepository


class HubAMontrekRepository(MontrekRepository):
    hub_class = bc_models.HubA

    def test_queryset_1(self):
        self.add_satellite_fields_annotations(
            bc_models.SatA1,
            [
                "field_a1_int",
            ],
            self.reference_date,
        )

        return super().build_queryset()


class HubBMontrekRepository(MontrekRepository):
    hub_class = bc_models.HubB


class TestMontrekRepository(TestCase):
    def test_build_queryset_with_satellite_fields(self):
        # Setup
        sat_a11 = bc_factories.SatA1Factory(
            state_date_end=montrek_time(2023, 7, 10),
            field_a1_int=5,
        )
        sat_a12 = bc_factories.SatA1Factory(
            hub_entity=sat_a11.hub_entity,
            state_date_start=montrek_time(2023, 7, 10),
            state_date_end=montrek_time(2023, 7, 20),
            field_a1_int=6,
        )
        sat_a13 = bc_factories.SatA1Factory(
            hub_entity=sat_a11.hub_entity,
            state_date_start=montrek_time(2023, 7, 20),
            field_a1_int=7,
        )
        sat_a21 = bc_factories.SatA2Factory(
            hub_entity=sat_a11.hub_entity,
            field_a2_float=8.0,
        )
        sat_a22 = bc_factories.SatA2Factory(
            state_date_end=montrek_time(2023, 7, 10),
            field_a2_float=9,
        )
        # Execute & test
        repository = HubAMontrekRepository(None)
        repository.reference_date = montrek_time(2023, 7, 8)
        queryset = repository.test_queryset_1()

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_a1_int, 5)
        self.assertEqual(queryset[1].field_a1_int, None)

    def test_build_queryset_with_linked_satellite_fields(self):
        ...

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
        self.add_satellite_fields_annotations(
            bc_models.SatA2,
            [
                "field_a2_float",
            ],
            self.reference_date,
        )
        return self.build_queryset()

    def test_queryset_2(self):
        self.add_linked_satellites_field_annotations(
            bc_models.SatB1,
            bc_models.LinkHubAHubB,
            ['field_b1_str'],
            self.reference_date,
        )
        return self.build_queryset()


class HubBMontrekRepository(MontrekRepository):
    hub_class = bc_models.HubB


class TestMontrekRepositorySatellite(TestCase):
    def setUp(self):
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
    def test_build_queryset_with_satellite_fields(self):
        repository = HubAMontrekRepository(None)
        repository.reference_date = montrek_time(2023, 7, 8)
        queryset = repository.test_queryset_1()

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_a1_int, 5)
        self.assertEqual(queryset[1].field_a1_int, None)
        self.assertEqual(queryset[0].field_a2_float, 8.0)
        self.assertEqual(queryset[1].field_a2_float, 9.0)

        repository.reference_date = montrek_time(2023, 7, 10)
        queryset = repository.test_queryset_1()

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_a1_int, 6)
        self.assertEqual(queryset[1].field_a1_int, None)
        self.assertEqual(queryset[0].field_a2_float, 8.0)
        self.assertEqual(queryset[1].field_a2_float, None)

        repository.reference_date = montrek_time(2023, 7, 15)
        queryset = repository.test_queryset_1()

        self.assertEqual(queryset[0].field_a1_int, 6)
        self.assertEqual(queryset[1].field_a1_int, None)
        self.assertEqual(queryset[0].field_a2_float, 8.0)
        self.assertEqual(queryset[1].field_a2_float, None)

        repository.reference_date = montrek_time(2023, 7, 20)
        queryset = repository.test_queryset_1()

        self.assertEqual(queryset[0].field_a1_int, 7)
        self.assertEqual(queryset[1].field_a1_int, None)
        self.assertEqual(queryset[0].field_a2_float, 8.0)
        self.assertEqual(queryset[1].field_a2_float, None)

class TestMontrekRepositoryLinks(TestCase):
    def setUp(self):
        huba1 = bc_factories.HubAFactory()
        huba2 = bc_factories.HubAFactory()
        hubb1 = bc_factories.HubBFactory()
        hubb2 = bc_factories.HubBFactory()
        hubc1 = bc_factories.HubCFactory()
        hubc2 = bc_factories.HubCFactory()

        bc_factories.LinkHubAHubBFactory(
            hub_in=huba1,
            hub_out=hubb1,
        )
        bc_factories.LinkHubAHubBFactory(
            hub_in=huba2,
            hub_out=hubb1,
            state_date_end=montrek_time(2023, 7, 12),
        )
        bc_factories.LinkHubAHubBFactory(
            hub_in=huba2,
            hub_out=hubb2,
            state_date_start=montrek_time(2023, 7, 12),
        )
        bc_factories.SatB1Factory(
            hub_entity=hubb1,
            state_date_end=montrek_time(2023, 7, 10),
            field_b1_str="First",
        )
        bc_factories.SatB1Factory(
            hub_entity=hubb1,
            state_date_start=montrek_time(2023, 7, 10),
            field_b1_str="Second",
        )
        bc_factories.SatB1Factory(
            hub_entity=hubb2,
            field_b1_str="Third",
        )
        
        bc_factories.LinkHubAHubCFactory(
            hub_in=huba1,
            hub_out=hubc1,
        )
        bc_factories.LinkHubAHubCFactory(
            hub_in=huba1,
            hub_out=hubc2,
            state_date_end=montrek_time(2023, 7, 12),
        )
        bc_factories.SatC1Factory(
            hub_entity=hubc1,
            field_c1_str="Multi1",
        )
        bc_factories.SatC1Factory(
            hub_entity=hubc2,
            field_c1_str="Multi2",
        )

    def test_many_to_one_link(self):
        repository = HubAMontrekRepository(None)
        repository.reference_date = montrek_time(2023, 7, 8)
        queryset = repository.test_queryset_2()

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].satb1__field_b1_str, "First")
        self.assertEqual(queryset[1].satb1__field_b1_str, "First")

        repository.reference_date = montrek_time(2023, 7, 10)
        queryset = repository.test_queryset_2()

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].satb1__field_b1_str, "Second")
        self.assertEqual(queryset[1].satb1__field_b1_str, "Second")

        repository.reference_date = montrek_time(2023, 7, 12)
        queryset = repository.test_queryset_2()

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].satb1__field_b1_str, "Second")
        self.assertEqual(queryset[1].satb1__field_b1_str, "Third")


    def test_many_to_many(self):
        ...

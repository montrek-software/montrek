from django.test import TestCase
from baseclasses.utils import montrek_time
from montrek_example.tests.factories import montrek_example_factories as me_factories
from baseclasses import models as me_models
from montrek_example.repositories.hub_a_repository import HubAMontrekRepository
from montrek_example.repositories.hub_b_repository import HubBMontrekRepository


class TestMontrekRepositorySatellite(TestCase):
    def setUp(self):
        sat_a11 = me_factories.SatA1Factory(
            state_date_end=montrek_time(2023, 7, 10),
            field_a1_int=5,
        )
        sat_a12 = me_factories.SatA1Factory(
            hub_entity=sat_a11.hub_entity,
            state_date_start=montrek_time(2023, 7, 10),
            state_date_end=montrek_time(2023, 7, 20),
            field_a1_int=6,
        )
        sat_a13 = me_factories.SatA1Factory(
            hub_entity=sat_a11.hub_entity,
            state_date_start=montrek_time(2023, 7, 20),
            field_a1_int=7,
        )
        sat_a21 = me_factories.SatA2Factory(
            hub_entity=sat_a11.hub_entity,
            field_a2_float=8.0,
        )
        sat_a22 = me_factories.SatA2Factory(
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
        huba1 = me_factories.HubAFactory()
        huba2 = me_factories.HubAFactory()
        hubb1 = me_factories.HubBFactory()
        hubb2 = me_factories.HubBFactory()
        hubc1 = me_factories.HubCFactory()
        hubc2 = me_factories.HubCFactory()

        me_factories.LinkHubAHubBFactory(
            hub_in=huba1,
            hub_out=hubb1,
        )
        me_factories.LinkHubAHubBFactory(
            hub_in=huba2,
            hub_out=hubb1,
            state_date_end=montrek_time(2023, 7, 12),
        )
        me_factories.LinkHubAHubBFactory(
            hub_in=huba2,
            hub_out=hubb2,
            state_date_start=montrek_time(2023, 7, 12),
        )
        me_factories.SatB1Factory(
            hub_entity=hubb1,
            state_date_end=montrek_time(2023, 7, 10),
            field_b1_str="First",
        )
        me_factories.SatB1Factory(
            hub_entity=hubb1,
            state_date_start=montrek_time(2023, 7, 10),
            field_b1_str="Second",
        )
        me_factories.SatB1Factory(
            hub_entity=hubb2,
            field_b1_str="Third",
        )
        
        me_factories.LinkHubAHubCFactory(
            hub_in=huba1,
            hub_out=hubc1,
        )
        me_factories.LinkHubAHubCFactory(
            hub_in=huba1,
            hub_out=hubc2,
            state_date_end=montrek_time(2023, 7, 12),
        )
        me_factories.SatC1Factory(
            hub_entity=hubc1,
            field_c1_str="Multi1",
        )
        me_factories.SatC1Factory(
            hub_entity=hubc2,
            field_c1_str="Multi2",
        )
        me_factories.SatA1Factory(
            hub_entity=huba1,
            field_a1_int=5,
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

    def test_link_reversed(self):
        repository = HubBMontrekRepository(None)
        repository.reference_date = montrek_time(2023, 7, 8)
        queryset = repository.test_queryset_1()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].sata1__field_a1_int, 5)
        self.assertEqual(queryset[1].sata1__field_a1_int, None)
        repository.reference_date = montrek_time(2023, 7, 15)
        queryset = repository.test_queryset_1()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].sata1__field_a1_int, 5)
        self.assertEqual(queryset[1].sata1__field_a1_int, None)

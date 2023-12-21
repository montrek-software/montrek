from django.test import TestCase
from django.utils import timezone
from django.utils import timezone
from baseclasses.utils import montrek_time
from montrek_example.tests.factories import montrek_example_factories as me_factories
from baseclasses import models as me_models
from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example import models as me_models


class TestMontrekRepositorySatellite(TestCase):
    def setUp(self):
        sat_a11 = me_factories.SatA1Factory(
            state_date_end=montrek_time(2023, 7, 10),
            field_a1_int=5,
        )
        me_factories.SatA1Factory(
            hub_entity=sat_a11.hub_entity,
            state_date_start=montrek_time(2023, 7, 10),
            state_date_end=montrek_time(2023, 7, 20),
            field_a1_int=6,
        )
        me_factories.SatA1Factory(
            hub_entity=sat_a11.hub_entity,
            state_date_start=montrek_time(2023, 7, 20),
            field_a1_int=7,
        )
        me_factories.SatA2Factory(
            hub_entity=sat_a11.hub_entity,
            field_a2_float=8.0,
        )
        me_factories.SatA2Factory(
            state_date_end=montrek_time(2023, 7, 10),
            field_a2_float=9,
        )

    def test_build_queryset_with_satellite_fields(self):
        repository = HubARepository(None)
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


class TestMontrekCreatObject(TestCase):
    def test_std_create_object_single_satellite(self):
        repository = HubARepository(None)
        repository.std_create_object({"field_a1_int": 5, "field_a1_str": "test"})
        self.assertEqual(me_models.SatA1.objects.count(), 1)
        self.assertEqual(me_models.SatA1.objects.first().field_a1_int, 5)
        self.assertEqual(me_models.SatA1.objects.first().field_a1_str, "test")
        self.assertEqual(me_models.HubA.objects.count(), 1)
        self.assertEqual(me_models.SatA2.objects.count(), 0)

    def test_std_create_object_multi_satellites(self):
        repository = HubARepository(None)
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
            }
        )
        self.assertEqual(me_models.SatA1.objects.count(), 1)
        self.assertEqual(me_models.SatA1.objects.first().field_a1_int, 5)
        self.assertEqual(me_models.SatA1.objects.first().field_a1_str, "test")
        self.assertEqual(me_models.HubA.objects.count(), 1)
        self.assertEqual(me_models.SatA2.objects.count(), 1)
        self.assertEqual(me_models.SatA2.objects.first().field_a2_float, 6.0)
        self.assertEqual(me_models.SatA2.objects.first().field_a2_str, "test2")

    def test_std_create_object_existing_object(self):
        repository = HubARepository(None)
        for _ in range(2):
            repository.std_create_object(
                {
                    "field_a1_int": 5,
                    "field_a1_str": "test",
                    "field_a2_float": 6.0,
                    "field_a2_str": "test2",
                }
            )
            self.assertEqual(me_models.SatA1.objects.count(), 1)
            self.assertEqual(me_models.SatA1.objects.first().field_a1_int, 5)
            self.assertEqual(me_models.SatA1.objects.first().field_a1_str, "test")
            self.assertEqual(me_models.HubA.objects.count(), 1)
            self.assertEqual(me_models.SatA2.objects.count(), 1)
            self.assertEqual(me_models.SatA2.objects.first().field_a2_float, 6.0)
            self.assertEqual(me_models.SatA2.objects.first().field_a2_str, "test2")

    def test_std_create_object_update_satellite_value_field(self):
        snapshot_time = timezone.now()
        repository = HubARepository(None)
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
            }
        )
        self.assertEqual(me_models.SatA1.objects.count(), 1)
        self.assertEqual(me_models.SatA1.objects.first().field_a1_int, 5)
        self.assertEqual(me_models.SatA1.objects.first().field_a1_str, "test")
        self.assertEqual(me_models.HubA.objects.count(), 1)
        self.assertEqual(me_models.SatA2.objects.count(), 1)
        self.assertEqual(me_models.SatA2.objects.first().field_a2_float, 6.0)
        self.assertEqual(me_models.SatA2.objects.first().field_a2_str, "test2")

        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 7.0,
                "field_a2_str": "test2",
            }
        )
        self.assertEqual(me_models.SatA1.objects.count(), 1)
        self.assertEqual(me_models.SatA1.objects.first().field_a1_int, 5)
        self.assertEqual(me_models.SatA1.objects.first().field_a1_str, "test")
        self.assertEqual(me_models.HubA.objects.count(), 1)
        self.assertEqual(me_models.SatA2.objects.count(), 2)
        updated_sat = me_models.SatA2.objects.last()
        self.assertEqual(updated_sat.field_a2_float, 7.0)
        self.assertEqual(updated_sat.field_a2_str, "test2")
        updated_sat.hub_entity = me_models.HubA.objects.first()
        self.assertGreater(updated_sat.state_date_start, snapshot_time)
        self.assertLess(
            me_models.SatA2.objects.first().state_date_end,
            timezone.make_aware(timezone.datetime.max),
        )

    def test_std_create_object_update_satellite_id_field(self):
        # Make sure there are no existings Hubs and Satellites
        self.assertEqual(me_models.SatA1.objects.count(), 0)
        self.assertEqual(me_models.SatA2.objects.count(), 0)
        self.assertEqual(me_models.HubA.objects.count(), 0)
        # Create one object
        repository = HubARepository(None)
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
            }
        )
        # Make sure there is one Hub and two Satellites
        self.assertEqual(me_models.SatA1.objects.count(), 1)
        self.assertEqual(me_models.SatA2.objects.count(), 1)
        self.assertEqual(me_models.HubA.objects.count(), 1)
        # Change the id of the first Satellite
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test_new",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
            }
        )
        # The std_queryset should return the adjusted object
        a_object = HubARepository().std_queryset().get()
        self.assertEqual(a_object.field_a1_str, "test_new")
        self.assertEqual(a_object.field_a1_int, 5)
        self.assertEqual(a_object.field_a2_str, "test2")
        self.assertEqual(a_object.field_a2_float, 6.0)

        # Now we have two hubs with different state_date_start and state_date_end:
        self.assertEqual(me_models.HubA.objects.count(), 2)
        self.assertEqual(
            me_models.HubA.objects.first().state_date_start,
            timezone.make_aware(timezone.datetime.min),
        )
        self.assertEqual(
            me_models.HubA.objects.last().state_date_end,
            timezone.make_aware(timezone.datetime.max),
        )
        self.assertEqual(
            me_models.HubA.objects.last().state_date_start,
            me_models.HubA.objects.first().state_date_end,
        )


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
        repository = HubARepository(None)
        repository.reference_date = montrek_time(2023, 7, 8)
        queryset = repository.test_queryset_2()

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_b1_str, "First")
        self.assertEqual(queryset[1].field_b1_str, "First")

        repository.reference_date = montrek_time(2023, 7, 10)
        queryset = repository.test_queryset_2()

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_b1_str, "Second")
        self.assertEqual(queryset[1].field_b1_str, "Second")

        repository.reference_date = montrek_time(2023, 7, 12)
        queryset = repository.test_queryset_2()

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_b1_str, "Second")
        self.assertEqual(queryset[1].field_b1_str, "Third")

    def test_link_reversed(self):
        repository = HubBRepository(None)
        repository.reference_date = montrek_time(2023, 7, 8)
        queryset = repository.test_queryset_1()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_a1_int, 5)
        self.assertEqual(queryset[1].field_a1_int, None)
        repository.reference_date = montrek_time(2023, 7, 15)
        queryset = repository.test_queryset_1()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_a1_int, 5)
        self.assertEqual(queryset[1].field_a1_int, None)

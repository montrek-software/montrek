from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.utils import timezone
from baseclasses.utils import montrek_time
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from montrek_example.tests.factories import montrek_example_factories as me_factories
from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.repositories.hub_c_repository import HubCRepository
from montrek_example.repositories.hub_d_repository import HubDRepository
from montrek_example import models as me_models
import pandas as pd


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
        repository = HubARepository()
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


class TestMontrekCreateObject(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()

    def test_std_create_object_single_satellite(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.std_create_object({"field_a1_int": 5, "field_a1_str": "test"})
        self.assertEqual(me_models.SatA1.objects.count(), 1)
        self.assertEqual(me_models.SatA1.objects.first().field_a1_int, 5)
        self.assertEqual(me_models.SatA1.objects.first().field_a1_str, "test")
        self.assertEqual(me_models.SatA1.objects.first().created_by_id, self.user.id)
        self.assertEqual(me_models.HubA.objects.count(), 1)
        self.assertEqual(me_models.SatA2.objects.count(), 0)

    def test_std_create_object_multi_satellites(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
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
        self.assertEqual(me_models.SatA1.objects.first().created_by_id, self.user.id)
        self.assertEqual(me_models.HubA.objects.count(), 1)
        self.assertEqual(me_models.SatA2.objects.count(), 1)
        self.assertEqual(me_models.SatA2.objects.first().field_a2_float, 6.0)
        self.assertEqual(me_models.SatA2.objects.first().field_a2_str, "test2")
        self.assertEqual(me_models.SatA2.objects.first().created_by_id, self.user.id)

    def test_std_create_object_existing_object(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
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
            self.assertEqual(
                me_models.SatA1.objects.first().created_by_id, self.user.id
            )
            self.assertEqual(me_models.HubA.objects.count(), 1)
            self.assertEqual(me_models.HubA.objects.first().created_by_id, self.user.id)
            self.assertEqual(me_models.SatA2.objects.count(), 1)
            self.assertEqual(me_models.SatA2.objects.first().field_a2_float, 6.0)
            self.assertEqual(me_models.SatA2.objects.first().field_a2_str, "test2")
            self.assertEqual(
                me_models.SatA2.objects.first().created_by_id, self.user.id
            )

    def test_std_create_object_existing_object_different_user(self):
        users = MontrekUserFactory.create_batch(2)
        for i in range(2):
            repository = HubARepository(session_data={"user_id": users[i].id})
            repository.std_create_object(
                {
                    "field_a1_int": 5,
                    "field_a1_str": "test",
                }
            )
            self.assertEqual(me_models.SatA1.objects.count(), 1)
            self.assertEqual(me_models.SatA1.objects.last().field_a1_int, 5)
            self.assertEqual(me_models.SatA1.objects.last().field_a1_str, "test")
            self.assertEqual(me_models.SatA1.objects.last().created_by_id, users[0].id)
            self.assertEqual(me_models.HubA.objects.count(), 1)
            self.assertEqual(me_models.HubA.objects.first().created_by_id, users[0].id)

    def test_std_create_object_existing_object_make_copy(self):
        # Since hub_entity_id is a identifier field for the HubB satellites, any entry with the same attributes will
        # create a copy rather than leaving the old one in place.
        repository = HubBRepository(session_data={"user_id": self.user.id})
        for i in range(2):
            repository.std_create_object(
                {
                    "field_b1_date": "2023-12-23",
                    "field_b1_str": "test",
                    "field_b2_choice": "CHOICE1",
                    "field_b2_str": "test2",
                }
            )
            self.assertEqual(me_models.SatB1.objects.count(), i + 1)
            self.assertEqual(
                me_models.SatB1.objects.last().field_b1_date,
                montrek_time(2023, 12, 23).date(),
            )
            self.assertEqual(me_models.SatB1.objects.last().field_b1_str, "test")
            self.assertEqual(me_models.HubB.objects.count(), i + 1)
            self.assertEqual(me_models.HubB.objects.last().created_by_id, self.user.id)
            self.assertEqual(me_models.SatB2.objects.count(), i + 1)
            self.assertEqual(me_models.SatB2.objects.last().field_b2_choice, "CHOICE1")
            self.assertEqual(me_models.SatB2.objects.last().field_b2_str, "test2")
            self.assertEqual(me_models.SatB1.objects.last().created_by_id, self.user.id)

    def test_std_create_object_update_satellite_value_field(self):
        snapshot_time = timezone.now()
        repository = HubARepository(session_data={"user_id": self.user.id})
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
        self.assertEqual(me_models.SatA1.objects.first().created_by_id, self.user.id)
        self.assertEqual(me_models.HubA.objects.count(), 1)
        self.assertEqual(me_models.HubA.objects.first().created_by_id, self.user.id)
        self.assertEqual(me_models.SatA2.objects.count(), 1)
        self.assertEqual(me_models.SatA2.objects.first().field_a2_float, 6.0)
        self.assertEqual(me_models.SatA2.objects.first().field_a2_str, "test2")
        self.assertEqual(me_models.SatA1.objects.first().created_by_id, self.user.id)

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
        self.assertEqual(me_models.SatA1.objects.first().created_by_id, self.user.id)
        self.assertEqual(me_models.HubA.objects.count(), 1)
        self.assertEqual(me_models.HubA.objects.first().created_by_id, self.user.id)
        self.assertEqual(me_models.SatA2.objects.count(), 2)
        updated_sat = me_models.SatA2.objects.last()
        self.assertEqual(updated_sat.field_a2_float, 7.0)
        self.assertEqual(updated_sat.field_a2_str, "test2")
        self.assertEqual(updated_sat.created_by_id, self.user.id)
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
        repository = HubARepository(session_data={"user_id": self.user.id})
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
        self.assertEqual(a_object.created_by_id, self.user.id)

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

    def test_std_create_object_update_satellite_id_field_keep_hub(self):
        # Create one object
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
            }
        )
        a_object = (
            HubARepository(session_data={"user_id": self.user.id}).std_queryset().get()
        )
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test_new",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
                "hub_entity_id": a_object.id,
            }
        )
        # We should still have one Hub
        self.assertEqual(me_models.HubA.objects.count(), 1)

        # The std_queryset should return the adjusted object
        b_object = HubARepository().std_queryset().get()
        self.assertEqual(b_object.field_a1_str, "test_new")

    def test_std_create_object_raises_error_for_missing_user_id(self):
        with self.assertRaises(PermissionDenied):
            HubARepository().std_create_object({})

    def test_std_create_object_comment(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
                "comment": "some comment",
            }
        )
        self.assertEqual(me_models.SatA1.objects.first().comment, "some comment")
        self.assertEqual(me_models.SatA2.objects.first().comment, "some comment")

        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
                "comment": "some new comment",
            }
        )
        # Comment change only when data changes
        self.assertEqual(me_models.SatA1.objects.last().comment, "some comment")
        self.assertEqual(me_models.SatA2.objects.last().comment, "some comment")
        repository.std_create_object(
            {
                "field_a1_int": 4,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
                "comment": "some new comment",
            }
        )
        self.assertEqual(me_models.SatA1.objects.last().comment, "some new comment")
        self.assertEqual(me_models.SatA2.objects.last().comment, "some comment")

    def test_create_objects_from_data_frame(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        data_frame = pd.DataFrame(
            {
                "field_a1_int": [5, 6],
                "field_a1_str": ["test", "test2"],
                "field_a2_float": [6.0, 7.0],
                "field_a2_str": ["test2", "test3"],
            }
        )
        repository.create_objects_from_data_frame(data_frame)
        self.assertEqual(me_models.HubA.objects.count(), 2)
        self.assertEqual(me_models.SatA1.objects.count(), 2)
        self.assertEqual(me_models.SatA2.objects.count(), 2)
        self.assertEqual(me_models.SatA1.objects.first().field_a1_int, 5)
        self.assertEqual(me_models.SatA1.objects.last().field_a1_int, 6)
        self.assertEqual(me_models.SatA1.objects.first().field_a1_str, "test")
        self.assertEqual(me_models.SatA1.objects.last().field_a1_str, "test2")
        self.assertEqual(me_models.SatA2.objects.first().field_a2_float, 6.0)
        self.assertEqual(me_models.SatA2.objects.last().field_a2_float, 7.0)
        self.assertEqual(me_models.SatA2.objects.first().field_a2_str, "test2")
        self.assertEqual(me_models.SatA2.objects.last().field_a2_str, "test3")
        self.assertEqual(me_models.HubA.objects.first().created_by_id, self.user.id)
        self.assertEqual(me_models.HubA.objects.last().created_by_id, self.user.id)

    def test_create_objects_from_data_frame_comment(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        data_frame = pd.DataFrame(
            {
                "field_a1_int": [5, 6],
                "field_a1_str": ["test", "test2"],
                "field_a2_float": [6.0, 7.0],
                "field_a2_str": ["test2", "test3"],
                "comment": "some_comment",
            }
        )
        repository.create_objects_from_data_frame(data_frame)
        for sat1 in me_models.SatA1.objects.all():
            self.assertEqual(sat1.comment, "some_comment")
        for sat2 in me_models.SatA2.objects.all():
            self.assertEqual(sat2.comment, "some_comment")

    def test_create_hub_a_with_link_to_hub_b(self):
        hub_b = me_factories.SatB1Factory().hub_entity
        self.assertEqual(me_models.HubB.objects.count(), 1)
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
                "link_hub_a_hub_b": hub_b,
            }
        )
        self.assertEqual(me_models.HubB.objects.count(), 1)
        self.assertEqual(me_models.HubA.objects.count(), 1)
        self.assertEqual(me_models.LinkHubAHubB.objects.count(), 1)
        self.assertEqual(me_models.HubA.objects.first().link_hub_a_hub_b.first(), hub_b)

    def test_create_hub_a_with_link_to_hub_b_update(self):
        sat_b_1 = me_factories.SatB1Factory()
        sat_b_2 = me_factories.SatB1Factory(field_b1_str="TEST")
        hub_b_1 = sat_b_1.hub_entity
        hub_b_2 = sat_b_2.hub_entity
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
                "link_hub_a_hub_b": hub_b_1,
            }
        )
        queried_object = repository.std_queryset().get()
        self.assertEqual(queried_object.field_b1_str, sat_b_1.field_b1_str)
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
                "link_hub_a_hub_b": hub_b_2,
            }
        )
        self.assertEqual(me_models.LinkHubAHubB.objects.count(), 2)
        first_linked_hub = me_models.LinkHubAHubB.objects.first()
        last_linked_hub = me_models.LinkHubAHubB.objects.last()
        self.assertEqual(first_linked_hub.hub_out, hub_b_1)
        self.assertEqual(last_linked_hub.hub_out, hub_b_2)
        self.assertEqual(
            first_linked_hub.state_date_end, last_linked_hub.state_date_start
        )
        queried_object = repository.std_queryset().get()
        self.assertEqual(queried_object.field_b1_str, sat_b_2.field_b1_str)

    def test_create_hub_a_with_link_to_hub_b_existing(self):
        sat_b_1 = me_factories.SatB1Factory()
        hub_b_1 = sat_b_1.hub_entity
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
                "link_hub_a_hub_b": hub_b_1,
            }
        )
        queried_object = repository.std_queryset().get()
        self.assertEqual(queried_object.field_b1_str, sat_b_1.field_b1_str)
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
                "link_hub_a_hub_b": hub_b_1,
            }
        )
        self.assertEqual(me_models.LinkHubAHubB.objects.count(), 1)
        queried_object = repository.std_queryset().get()
        self.assertEqual(queried_object.field_b1_str, sat_b_1.field_b1_str)


class TestDeleteObject(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()

    def test_delete_object(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.std_create_object({"field_a1_int": 5, "field_a1_str": "test"})
        self.assertEqual(me_models.SatA1.objects.count(), 1)
        self.assertEqual(me_models.HubA.objects.count(), 1)
        deletion_object = repository.std_queryset().get()
        repository.std_delete_object(deletion_object)
        self.assertEqual(me_models.SatA1.objects.count(), 1)
        self.assertEqual(me_models.HubA.objects.count(), 1)
        self.assertEqual(len(repository.std_queryset()), 0)


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
        repository = HubARepository()
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
        repository = HubBRepository()
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


class TestTimeSeries(TestCase):
    def setUp(self) -> None:
        ts_satellite_c1 = me_factories.SatC1Factory.create(
            field_c1_str="Hallo",
            field_c1_bool=True,
        )
        me_factories.SatTSC2Factory.create(
            hub_entity=ts_satellite_c1.hub_entity,
            field_tsc2_float=1.0,
            value_date=montrek_time(2024, 2, 5),
        )
        self.user = MontrekUserFactory()

    def test_existing_satellite(self):
        repository = HubCRepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "field_c1_str": "Hallo",
                "field_c1_bool": True,
                "field_tsc2_float": 1.0,
                "value_date": montrek_time(2024, 2, 5),
            }
        )
        queryset = me_models.SatTSC2.objects.all()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].field_tsc2_float, 1.0)
        self.assertEqual(queryset[0].value_date, montrek_time(2024, 2, 5).date())

    def test_update_satellite(self):
        repository = HubCRepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "field_c1_str": "Hallo",
                "field_c1_bool": True,
                "field_tsc2_float": 2.0,
                "value_date": montrek_time(2024, 2, 5),
            }
        )
        queryset = me_models.SatTSC2.objects.all()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_tsc2_float, 1.0)
        self.assertEqual(queryset[0].value_date, montrek_time(2024, 2, 5).date())
        self.assertEqual(queryset[1].field_tsc2_float, 2.0)
        self.assertEqual(queryset[1].value_date, montrek_time(2024, 2, 5).date())
        self.assertEqual(queryset[0].state_date_end, queryset[1].state_date_start)

    def test_new_satellite(self):
        repository = HubCRepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "field_c1_str": "Hallo",
                "field_c1_bool": True,
                "field_tsc2_float": 3.0,
                "value_date": montrek_time(2024, 2, 6),
            }
        )
        queryset = me_models.SatTSC2.objects.all()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_tsc2_float, 1.0)
        self.assertEqual(queryset[0].value_date, montrek_time(2024, 2, 5).date())
        self.assertEqual(queryset[1].field_tsc2_float, 3.0)
        self.assertEqual(queryset[1].value_date, montrek_time(2024, 2, 6).date())
        self.assertEqual(queryset[1].created_by_id, self.user.id)
        for i in range(2):
            self.assertEqual(
                queryset[i].state_date_end,
                timezone.make_aware(timezone.datetime.max),
            )
            self.assertLess(queryset[i].state_date_start, timezone.now())

    def test_build_time_series_queryset_wrong_satellite_class(self):
        repository = HubCRepository()
        with self.assertRaisesRegex(
            ValueError,
            "SatC1 is not a subclass of MontrekTimeSeriesSatelliteABC",
        ):
            repository.build_time_series_queryset(
                me_models.SatC1,
                montrek_time(2024, 2, 5),
            )

    def test_build_time_series_queryset(self):
        me_factories.SatTSC2Factory.create_batch(3)
        test_query = HubCRepository().build_time_series_queryset(
            me_models.SatTSC2,
            montrek_time(2024, 2, 5),
        )
        self.assertEqual(test_query.count(), 4)


class TestHistory(TestCase):
    def setUp(self) -> None:
        self.user = MontrekUserFactory()

    def test_history_one_satellite(self):
        huba = me_factories.HubAFactory()
        me_factories.SatA1Factory(
            hub_entity=huba,
            field_a1_str="TestFeld",
            field_a1_int=5,
            state_date_end=montrek_time(2024, 2, 17),
            created_by=self.user,
        )
        me_factories.SatA1Factory(
            hub_entity=huba,
            field_a1_str="TestFeld",
            field_a1_int=6,
            state_date_start=montrek_time(2024, 2, 17),
            created_by=self.user,
            comment="some comment",
        )
        me_factories.SatA2Factory(
            hub_entity=huba,
            field_a2_str="ConstantTestFeld",
            field_a2_float=6.0,
            created_by=self.user,
        )
        hubb = me_factories.HubBFactory()
        huba.link_hub_a_hub_b.add(hubb)
        repository = HubARepository()

        test_querysets_dict = repository.get_history_queryset(huba.id)

        self.assertEqual(len(test_querysets_dict), 3)
        sata1_queryset = test_querysets_dict["SatA1"]
        self.assertEqual(sata1_queryset.count(), 2)
        self.assertEqual(sata1_queryset[1].field_a1_int, 5)
        self.assertEqual(sata1_queryset[0].field_a1_int, 6)
        self.assertEqual(sata1_queryset[0].changed_by, self.user.email)
        self.assertEqual(sata1_queryset[1].changed_by, self.user.email)
        self.assertEqual(sata1_queryset[0].comment, "some comment")
        sat_a2_queryset = test_querysets_dict["SatA2"]
        self.assertEqual(sat_a2_queryset.count(), 1)
        self.assertEqual(sat_a2_queryset[0].field_a2_float, 6.0)
        self.assertEqual(sat_a2_queryset[0].field_a2_str, "ConstantTestFeld")
        self.assertEqual(sat_a2_queryset[0].changed_by, self.user.email)

        link_queryset = test_querysets_dict["LinkHubAHubB"]
        self.assertEqual(link_queryset.count(), 1)
        self.assertEqual(link_queryset[0].hub_out, hubb)


class TestMontrekManyToManyRelations(TestCase):
    def setUp(self) -> None:
        self.user = MontrekUserFactory()
        self.satb1 = me_factories.SatB1Factory(
            field_b1_str="First",
        )
        self.satb2 = me_factories.SatB1Factory(
            field_b1_str="Second",
        )

        self.satd1 = me_factories.SatD1Factory(
            field_d1_str="erster",
            field_d1_int=1,
        )
        self.satd2 = me_factories.SatD1Factory(
            field_d1_str="zwoter",
            field_d1_int=2,
        )
        me_factories.LinkHubBHubDFactory.create(
            hub_in=self.satb1.hub_entity,
            hub_out=self.satd1.hub_entity,
        )
        me_factories.LinkHubBHubDFactory.create(
            hub_in=self.satb1.hub_entity,
            hub_out=self.satd2.hub_entity,
        )
        me_factories.LinkHubBHubDFactory.create(
            hub_in=self.satb2.hub_entity,
            hub_out=self.satd1.hub_entity,
        )

    def test_return_many_to_many_relation(self):
        repository_b = HubBRepository()
        satb_queryset = repository_b.std_queryset()
        self.assertEqual(satb_queryset.count(), 2)
        satb_queryset = satb_queryset.order_by("field_b1_str")
        self.assertEqual(
            satb_queryset[0].field_d1_str,
            f"{self.satd1.field_d1_str},{self.satd2.field_d1_str}",
        )
        self.assertEqual(
            satb_queryset[0].field_d1_int,
            f"{self.satd1.field_d1_int},{self.satd2.field_d1_int}",
        )
        self.assertEqual(satb_queryset[1].field_d1_str, self.satd1.field_d1_str)
        repository_d = HubDRepository()
        satd_queryset = repository_d.std_queryset()
        self.assertEqual(satd_queryset.count(), 2)
        self.assertEqual(
            satd_queryset[0].field_b1_str,
            f"{self.satb1.field_b1_str},{self.satb2.field_b1_str}",
        )
        self.assertEqual(satd_queryset[1].field_b1_str, self.satb1.field_b1_str)

    def test_add_new_many_to_many_relation(self):
        input_data = {
            "field_b1_str": "Hallo",
            "field_b1_date": montrek_time(2024, 3, 26),
            "link_hub_b_hub_d": [self.satd1.hub_entity, self.satd2.hub_entity],
        }
        repository_b = HubBRepository(session_data={"user_id": self.user.id})
        new_sat_b = repository_b.std_create_object(input_data)
        links = new_sat_b.link_hub_b_hub_d.all()
        self.assertEqual(links.count(), 2)
        self.assertEqual(links[0], self.satd1.hub_entity)
        self.assertEqual(links[1], self.satd2.hub_entity)

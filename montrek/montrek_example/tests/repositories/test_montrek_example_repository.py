import datetime

import pandas as pd
from baseclasses.utils import montrek_time
from baseclasses.errors.montrek_user_error import MontrekError
from django.core.exceptions import PermissionDenied
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from user.tests.factories.montrek_user_factories import MontrekUserFactory

from montrek_example import models as me_models
from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.repositories.hub_c_repository import HubCRepository
from montrek_example.repositories.hub_d_repository import HubDRepository
from montrek_example.tests.factories import montrek_example_factories as me_factories

MIN_DATE = timezone.make_aware(timezone.datetime.min)
MAX_DATE = timezone.make_aware(timezone.datetime.max)


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

    def test_get_all_fields(self):
        repo = HubARepository()
        repo.calculated_fields += ["dummy1", "dummy2"]
        test_fields = repo.get_all_fields()
        self.assertEqual(
            test_fields,
            [
                "comment",
                "field_a1_str",
                "field_a1_int",
                "comment",
                "field_a2_str",
                "field_a2_float",
                "dummy1",
                "dummy2",
                "field_b1_str",
            ],
        )

    def test_get_all_annotated_fields(self):
        repo = HubARepository()
        repo.add_linked_satellites_field_annotations(
            me_models.SatTSC2,
            me_models.LinkHubAHubC,
            ["field_tsc2_float"],
            last_ts_value=True,
        )  # linked time series field
        repo.std_queryset()
        repo.rename_field("field_a1_str", "my_field_a1_str")  # direct satellite field
        repo.rename_field("field_b1_str", "my_field_b1_str")  # linked field
        test_fields = repo.get_all_annotated_fields()
        self.assertEqual(
            test_fields,
            [
                "field_tsc2_float",
                "field_a1_int",
                "field_a2_float",
                "field_a2_str",
                "my_field_a1_str",
                "my_field_b1_str",
            ],
        )
        # direct time series satellite fields
        repo = HubCRepository()
        test_fields = repo.get_all_annotated_fields()
        self.assertEqual(
            test_fields,
            [
                "field_c1_bool",
                "field_c1_str",
                "field_tsd2_float",
                "field_tsd2_int",
                "field_tsc2_float",
                "value_date",
                "field_tsc3_int",
                "field_tsc3_str",
                "field_tsc4_int",
            ],
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
        self.assertGreater(
            me_models.HubA.objects.first().state_date_start,
            MIN_DATE,
        )
        self.assertEqual(
            me_models.HubA.objects.last().state_date_end,
            MAX_DATE,
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

    def test_create_objects_from_data_frame_duplicate(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        data_frame = pd.DataFrame(
            {
                "field_a1_int": [5, 6, 7],
                "field_a1_str": ["test", "test2", "test"],
                "field_a2_float": [6.0, 7.0, 8.0],
                "field_a2_str": ["test2", "test3", "test4"],
            }
        )
        self.assertRaises(
            ValueError, repository.create_objects_from_data_frame, data_frame
        )

    def test_raise_error_for_duplicates_with_hub_entity_id(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        test_hub = me_factories.HubAFactory()
        data_frame = pd.DataFrame(
            {
                "hub_entity_id": [test_hub.id, test_hub.id],
                "field_a1_str": ["test", "test2"],
            }
        )
        self.assertRaises(
            ValueError, repository.create_objects_from_data_frame, data_frame
        )

    def test_raise_no_error_for_duplicates_with_hub_entity_id_and_value_date(self):
        repository = HubCRepository(session_data={"user_id": self.user.id})
        test_hub = me_factories.HubCFactory()
        data_frame = pd.DataFrame(
            {
                "hub_entity_id": [test_hub.id, test_hub.id],
                "field_tsc3_str": ["test", "test2"],
                "value_date": [datetime.date(2023, 1, 1), datetime.date(2023, 1, 2)],
            }
        )
        repository.create_objects_from_data_frame(data_frame)

    def test_raise_error_for_duplicates_with_hub_entity_id_and_value_date(self):
        repository = HubCRepository(session_data={"user_id": self.user.id})
        test_hub = me_factories.HubCFactory()
        data_frame = pd.DataFrame(
            {
                "hub_entity_id": [test_hub.id, test_hub.id],
                "field_tsc3_str": ["test", "test2"],
                "value_date": [datetime.date(2023, 1, 1), datetime.date(2023, 1, 1)],
            }
        )
        self.assertRaises(
            ValueError, repository.create_objects_from_data_frame, data_frame
        )

    def test_create_objects_from_data_frame_duplicate_drop(self):
        # If rows in the data frame are duplicates, they should be dropped.
        repository = HubARepository(session_data={"user_id": self.user.id})
        data_frame = pd.DataFrame(
            {
                "field_a1_int": [5, 6, 5],
                "field_a1_str": ["test", "test2", "test"],
                "field_a2_float": [6.0, 7.0, 6.0],
                "field_a2_str": ["test4", "test3", "test4"],
            }
        )
        repository.create_objects_from_data_frame(data_frame)
        test_query = repository.std_queryset()
        self.assertEqual(test_query.count(), 2)

    def test_create_objects_from_data_frame_drop_empty_rows(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        data_frame = pd.DataFrame(
            {
                "field_a1_int": [5, None, 5],
                "field_a1_str": ["test", None, "test2"],
                "field_a2_float": [6.0, None, 6.0],
                "field_a2_str": ["test4", None, None],
            }
        )
        repository.create_objects_from_data_frame(data_frame)
        test_query = repository.std_queryset()
        self.assertEqual(test_query.count(), 2)
        self.assertEqual(test_query[0].field_a1_int, 5)
        self.assertEqual(repository.messages[0].message, "1 empty rows not uploaded!")

    def test_create_objects_from_data_frame_missing_primary_satellite_identifier_column(
        self,
    ):
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.std_queryset()
        # A missing field_a1_str column should hot raise an error.
        data_frame = pd.DataFrame(
            {
                "field_a2_float": [6.0, 7.0, 8.0],
                "field_a2_str": ["test2", "test3", "test4"],
            }
        )
        repository.create_objects_from_data_frame(data_frame)
        queryset = repository.std_queryset()
        self.assertEqual(queryset.count(), 3)

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

    def test_create_objects_from_data_frame__static_and_ts_data(self):
        repository = HubCRepository(session_data={"user_id": self.user.id})
        hub1 = me_factories.HubCFactory()
        hub2 = me_factories.HubCFactory()
        data_frame = pd.DataFrame(
            {
                "hub_entity_id": [hub1.id, hub1.id, hub2.id],
                "field_c1_str": ["test_static", "test_static", "test_static2"],
                "field_c1_bool": [True, True, False],
                "value_date": ["2024-08-01", "2024-08-02", "2024-08-02"],
                "field_tsc2_float": [6.0, 7.0, 8.0],
                "field_tsc3_int": [1, 2, 3],
                "field_tsc3_str": ["test", "test2", "test3"],
                "field_tsc4_int": [4, 5, 6],
            }
        )
        repository.create_objects_from_data_frame(data_frame)
        test_query = repository.std_queryset()
        self.assertEqual(test_query.count(), 3)
        self.assertEqual(me_models.HubC.objects.count(), 2)
        self.assertEqual(me_models.SatC1.objects.count(), 2)

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

    def test_write_zeros_to_db(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 0.0,
                "field_a2_str": "test2",
            }
        )
        queried_object = repository.std_queryset().get()
        self.assertEqual(queried_object.field_a2_float, 0.0)

    def test_create_with_nan_in_data_frame(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        data_frame = pd.DataFrame(
            {
                "field_a1_int": [5, 6, 7],
                "field_a1_str": ["test", "test2", "test3"],
                "field_a2_float": [6.0, 7.0, 8.0],
                "field_a2_str": ["test2", "test3", pd.NA],
            }
        )
        repository.create_objects_from_data_frame(data_frame)
        test_query = repository.std_queryset()
        self.assertEqual(test_query.count(), 3)

    def test__is_built(self):
        montrek_repo = HubARepository()
        self.assertFalse(montrek_repo._is_built)
        montrek_repo.std_queryset()
        self.assertTrue(montrek_repo._is_built)


class TestMontrekCreateObjectTransaction(TransactionTestCase):
    def setUp(self):
        self.user = MontrekUserFactory()

    def test_std_create_object_is_atomic(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        with self.assertRaises(ValueError):
            repository.std_create_object({"field_a1_int": "test"})
        self.assertEqual(me_models.SatA1.objects.count(), 0)
        self.assertEqual(me_models.HubA.objects.count(), 0)


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
        self.assertLess(me_models.SatA1.objects.first().state_date_end, timezone.now())
        self.assertEqual(me_models.HubA.objects.count(), 1)
        self.assertEqual(len(repository.std_queryset()), 0)

    def test_reintroduce_deleted_object(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.std_create_object({"field_a1_int": 5, "field_a1_str": "test"})
        deletion_object = repository.std_queryset().get()
        repository.std_delete_object(deletion_object)
        repository.std_create_object({"field_a1_int": 5, "field_a1_str": "test"})
        self.assertEqual(me_models.SatA1.objects.count(), 2)
        self.assertEqual(me_models.HubA.objects.count(), 2)
        self.assertEqual(len(repository.std_queryset()), 1)


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
        self.sat_c_1 = me_factories.SatC1Factory(
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


class TestLinkOneToOneUpates(TestCase):
    def setUp(self):
        user = MontrekUserFactory()
        session_data = {"user_id": user.id}
        self.repository = HubARepository(session_data=session_data)
        self.hub_a = me_factories.HubAFactory()
        self.hub_b = me_factories.HubBFactory()
        me_factories.LinkHubAHubBFactory(hub_in=self.hub_a, hub_out=self.hub_b)

    def test_setup(self):
        links = me_models.LinkHubAHubB.objects.all()
        self.assertEqual(links.count(), 1)
        link = links.first()
        self.assertEqual(link.hub_out, self.hub_b)
        self.assertEqual(link.state_date_start, MIN_DATE)
        self.assertEqual(link.state_date_end, MAX_DATE)

    def test_update_one_to_one_link_same(self):
        # Adding the same link should not change anything
        self.repository.std_create_object(
            {
                "hub_entity_id": self.hub_a.id,
                "link_hub_a_hub_b": self.hub_b,
            }
        )
        links = me_models.LinkHubAHubB.objects.all()
        self.assertEqual(links.count(), 1)
        link = links.first()
        self.assertEqual(link.hub_out, self.hub_b)
        self.assertEqual(link.state_date_start, MIN_DATE)
        self.assertEqual(link.state_date_end, MAX_DATE)

    def test_update_one_to_one_link_different(self):
        hub_b2 = me_factories.HubBFactory()
        # Adding the a new link should create a new link with adjusted state dates
        self.repository.std_create_object(
            {
                "hub_entity_id": self.hub_a.id,
                "link_hub_a_hub_b": hub_b2,
            }
        )
        links = me_models.LinkHubAHubB.objects.all()
        self.assertEqual(links.count(), 2)
        link_1 = links.first()
        link_2 = links.last()
        self.assertEqual(link_1.hub_out, self.hub_b)
        self.assertEqual(link_2.hub_out, hub_b2)
        self.assertEqual(link_1.state_date_start, MIN_DATE)
        self.assertEqual(link_1.state_date_end, link_2.state_date_start)
        self.assertEqual(link_2.state_date_end, MAX_DATE)

    def test_more_than_one_link_is_created(self):
        hub_b2 = me_factories.HubBFactory()
        # Adding two links, only the first is considered the correct one
        # Since the first one is the same as the existing one, it should not be changed
        import_df = pd.DataFrame(
            {
                "hub_entity_id": [self.hub_a.id, self.hub_a.id],
                "link_hub_a_hub_b": [self.hub_b, hub_b2],
            }
        )
        self.repository.create_objects_from_data_frame(import_df)
        links = me_models.LinkHubAHubB.objects.all()
        self.assertEqual(links.count(), 1)
        link_1 = links.first()
        self.assertEqual(link_1.hub_out, self.hub_b)
        # When a different link is added, the existing one should be replaced by the new one
        import_df = pd.DataFrame(
            {
                "hub_entity_id": [self.hub_a.id, self.hub_a.id],
                "link_hub_a_hub_b": [hub_b2, self.hub_b],
            }
        )
        self.repository.create_objects_from_data_frame(import_df)
        links = me_models.LinkHubAHubB.objects.all()
        self.assertEqual(links.count(), 2)
        link_1 = links.first()
        link_2 = links.last()
        self.assertEqual(link_1.hub_out, self.hub_b)
        self.assertEqual(link_2.hub_out, hub_b2)
        self.assertEqual(link_1.state_date_start, MIN_DATE)
        self.assertEqual(link_1.state_date_end, link_2.state_date_start)
        self.assertEqual(link_2.state_date_end, MAX_DATE)

    def test_more_than_one_link_is_created__raise_error_on_one_line(self):
        hub_b2 = me_factories.HubBFactory()
        # Adding two links, only the first is considered the correct one
        # Since the first one is the same as the existing one, it should not be changed
        import_df = pd.DataFrame(
            {
                "hub_entity_id": [self.hub_a.id],
                "link_hub_a_hub_b": [[self.hub_b, hub_b2]],
            }
        )
        with self.assertRaises(MontrekError):
            self.repository.create_objects_from_data_frame(import_df)


class TestLinkOneToManyUpates(TestCase):
    def setUp(self):
        user = MontrekUserFactory()
        session_data = {"user_id": user.id}
        self.repository = HubARepository(session_data=session_data)
        self.hub_a = me_factories.HubAFactory()
        self.hub_c = me_factories.HubCFactory()
        me_factories.LinkHubAHubCFactory(hub_in=self.hub_a, hub_out=self.hub_c)

    def test_setup(self):
        links = me_models.LinkHubAHubC.objects.all()
        self.assertEqual(links.count(), 1)
        link = links.first()
        self.assertEqual(link.hub_out, self.hub_c)
        self.assertEqual(link.state_date_start, MIN_DATE)
        self.assertEqual(link.state_date_end, MAX_DATE)

    def test_update_one_to_many_link_same(self):
        # Adding the same link should not change anything
        self.repository.std_create_object(
            {
                "hub_entity_id": self.hub_a.id,
                "link_hub_a_hub_c": self.hub_c,
            }
        )
        links = me_models.LinkHubAHubC.objects.all()
        self.assertEqual(links.count(), 1)
        link = links.first()
        self.assertEqual(link.hub_out, self.hub_c)
        self.assertEqual(link.state_date_start, MIN_DATE)
        self.assertEqual(link.state_date_end, MAX_DATE)

    def test_update_one_to_many_link_different(self):
        hub_c2 = me_factories.HubCFactory()
        # Adding the a new link should create a new link with adjusted state dates
        # Both links should exist at the same time
        self.repository.std_create_object(
            {
                "hub_entity_id": self.hub_a.id,
                "link_hub_a_hub_c": hub_c2,
            }
        )
        links = me_models.LinkHubAHubC.objects.all()
        self.assertEqual(links.count(), 2)
        link_1 = links.first()
        link_2 = links.last()
        self.assertEqual(link_1.hub_out, self.hub_c)
        self.assertEqual(link_2.hub_out, hub_c2)
        self.assertEqual(link_1.state_date_start, MIN_DATE)
        self.assertEqual(link_1.state_date_end, MAX_DATE)
        self.assertEqual(link_2.state_date_end, MAX_DATE)
        self.assertGreater(link_2.state_date_start, MIN_DATE)

    def test_more_than_one_link_is_created_single_line(self):
        hub_c2 = me_factories.HubCFactory()
        import_df = pd.DataFrame(
            {
                "hub_entity_id": [self.hub_a.id],
                "link_hub_a_hub_c": [[self.hub_c, hub_c2]],
            }
        )
        self.repository.create_objects_from_data_frame(import_df)
        links = me_models.LinkHubAHubC.objects.all()
        self.assertEqual(links.count(), 2)
        link_1 = links.first()
        link_2 = links.last()
        self.assertEqual(link_1.hub_out, self.hub_c)
        self.assertEqual(link_2.hub_out, hub_c2)
        self.assertEqual(link_1.state_date_start, MIN_DATE)
        self.assertEqual(link_1.state_date_end, MAX_DATE)
        self.assertEqual(link_2.state_date_end, MAX_DATE)
        self.assertGreater(link_2.state_date_start, MIN_DATE)

    def test_duplicate_links_are_ignored(self):
        hub_c2 = me_factories.HubCFactory()
        linked_hubs = [self.hub_c, hub_c2]
        original_row = {
            "hub_entity_id": self.hub_a.id,
            "link_hub_a_hub_c": linked_hubs,
        }
        different_link_order_row = {
            "hub_entity_id": self.hub_a.id,
            "link_hub_a_hub_c": list(reversed(linked_hubs)),
        }
        import_df = pd.DataFrame(
            [
                original_row,
                different_link_order_row,
                original_row,
            ]
        )
        self.repository.create_objects_from_data_frame(import_df)
        links = me_models.LinkHubAHubC.objects.all()
        self.assertEqual(links.count(), 2)
        link_1 = links.first()
        link_2 = links.last()
        self.assertEqual(link_1.hub_out, self.hub_c)
        self.assertEqual(link_2.hub_out, hub_c2)
        self.assertEqual(link_1.state_date_start, MIN_DATE)
        self.assertEqual(link_1.state_date_end, MAX_DATE)
        self.assertEqual(link_2.state_date_end, MAX_DATE)
        self.assertGreater(link_2.state_date_start, MIN_DATE)


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

    def test_time_series_link_to_time_series(self):
        value_dates = [montrek_time(2024, 9, 18), montrek_time(2024, 9, 19)]
        for i, value_date in enumerate(value_dates):
            sat_c = me_factories.SatTSC2Factory.create(
                field_tsc2_float=i * 0.1,
                value_date=value_date,
            )
            sat_d = me_factories.SatTSD2Factory.create(
                field_tsd2_float=i * 0.2,
                field_tsd2_int=i,
                value_date=value_date,
            )
            sat_c.hub_entity.link_hub_c_hub_d.add(sat_d.hub_entity)
        repository = HubCRepository(session_data={"user_id": self.user.id})
        test_query = repository.std_queryset().filter(value_date__in=value_dates)
        self.assertEqual(test_query.count(), 2)
        self.assertEqual(test_query[1].field_tsc2_float, 0.0)
        self.assertEqual(test_query[1].field_tsd2_float, 0)
        self.assertEqual(test_query[1].field_tsd2_int, 0)
        self.assertEqual(test_query[0].field_tsc2_float, 0.1)
        self.assertEqual(test_query[0].field_tsd2_float, 0.2)
        self.assertEqual(test_query[0].field_tsd2_int, 1)


class TestTimeSeriesRepositoryEmpty(TestCase):
    def test_empty_time_series(self):
        repository = HubCRepository()
        queryset = repository.std_queryset()
        self.assertEqual(queryset.count(), 0)
        queryset.filter(field_tsc2_float__isnull=True)

    def test_first_container_empty(self):
        repository = HubCRepository()
        me_factories.SatTSC3Factory.create(
            field_tsc3_str="Test",
            value_date=montrek_time(2024, 2, 5),
            field_tsc3_int=5,
        )
        qs = repository.std_queryset()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].field_tsc3_str, "Test")
        self.assertEqual(qs[0].field_tsc3_int, 5)


class TestTimeSeriesQuerySet(TestCase):
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
        static_sats = me_factories.SatC1Factory.create_batch(3)
        self.ts_fact = me_factories.SatTSC2Factory.create(
            hub_entity=static_sats[0].hub_entity,
            field_tsc2_float=1.0,
            value_date=montrek_time(2024, 2, 5),
            state_date_end=montrek_time(2024, 7, 6),
        )
        self.ts_fact2 = me_factories.SatTSC2Factory.create(
            hub_entity=static_sats[0].hub_entity,
            field_tsc2_float=3.0,
            value_date=montrek_time(2024, 2, 5),
            state_date_start=montrek_time(2024, 7, 6),
        )
        me_factories.SatTSC2Factory.create(
            hub_entity=static_sats[0].hub_entity, value_date=montrek_time(2024, 2, 6)
        )
        me_factories.SatTSC2Factory.create(
            hub_entity=static_sats[1].hub_entity, value_date=montrek_time(2024, 2, 5)
        )
        self.user = MontrekUserFactory()

    def test_build_time_series_queryset_wrong_satellite_class(self):
        repository = HubCRepository()
        with self.assertRaisesRegex(
            ValueError,
            "SatC1 is not a subclass of MontrekTimeSeriesSatelliteABC",
        ):
            repository.build_time_series_queryset_container(
                me_models.SatC1,
                montrek_time(2024, 2, 5),
            ).queryset

    def test_build_time_series_queryset(self):
        repo = HubCRepository()
        test_query = repo.build_time_series_queryset_container(
            me_models.SatTSC2,
            ["field_tsc2_float"],
        ).queryset
        self.assertEqual(test_query.count(), 5)
        self.assertEqual(test_query[1].field_tsc2_float, self.ts_fact2.field_tsc2_float)
        self.assertEqual(test_query[4].field_tsc2_float, None)

    def test_build_time_series_queryset__reference_date_filter(self):
        repo = HubCRepository()
        repo.reference_date = montrek_time(2024, 7, 1)
        test_query = repo.build_time_series_queryset_container(
            me_models.SatTSC2,
            ["field_tsc2_float"],
        ).queryset
        self.assertEqual(test_query.count(), 5)
        self.assertEqual(test_query[1].field_tsc2_float, self.ts_fact.field_tsc2_float)
        self.assertEqual(test_query[4].field_tsc2_float, None)

    def test_build_time_series_queryset__session_dates(self):
        for end_date, expected_count in [
            (datetime.datetime(2024, 2, 1), 1),
            (datetime.datetime(2024, 2, 5), 4),
            (datetime.datetime(2024, 2, 6), 5),
            (datetime.datetime(2024, 2, 7), 5),
        ]:
            repo = HubCRepository(session_data={"end_date": end_date})
            test_query = repo.build_time_series_queryset_container(
                me_models.SatTSC2,
                ["field_tsc2_float"],
            ).queryset
            self.assertEqual(test_query.count(), expected_count)
        for start_date, expected_count in [
            (datetime.datetime(2024, 2, 1), 5),
            (datetime.datetime(2024, 2, 5), 5),
            (datetime.datetime(2024, 2, 6), 2),
            (datetime.datetime(2024, 2, 7), 1),
        ]:
            repo = HubCRepository(session_data={"start_date": start_date})
            test_query = repo.build_time_series_queryset_container(
                me_models.SatTSC2,
                ["field_tsc2_float"],
            ).queryset
            self.assertEqual(test_query.count(), expected_count)


class TestTimeSeriesStdQueryset(TestCase):
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
        static_sats = me_factories.SatC1Factory.create_batch(3)
        static_sats[0].field_c1_str = "Test"
        static_sats[0].save()
        me_factories.SatTSC2Factory.create(
            hub_entity=static_sats[0].hub_entity,
            field_tsc2_float=2.0,
            value_date=montrek_time(2024, 2, 5),
            state_date_end=montrek_time(2024, 7, 6),
        )
        me_factories.SatTSC2Factory.create(
            hub_entity=static_sats[0].hub_entity,
            field_tsc2_float=3.0,
            value_date=montrek_time(2024, 2, 5),
            state_date_start=montrek_time(2024, 7, 6),
        )
        me_factories.SatTSC2Factory.create(
            hub_entity=static_sats[0].hub_entity,
            value_date=montrek_time(2024, 2, 6),
            field_tsc2_float=2.5,
        )
        me_factories.SatTSC2Factory.create(
            hub_entity=static_sats[1].hub_entity,
            value_date=montrek_time(2024, 2, 5),
            field_tsc2_float=3.5,
        )
        me_factories.SatTSC3Factory.create(
            hub_entity=static_sats[0].hub_entity,
            value_date=montrek_time(2024, 2, 6),
            field_tsc3_int=5,
            field_tsc3_str="what1",
        )
        me_factories.SatTSC3Factory.create(
            hub_entity=static_sats[1].hub_entity,
            value_date=montrek_time(2024, 2, 5),
            field_tsc3_int=7,
            field_tsc3_str="what2",
        )
        me_factories.SatTSC3Factory.create(
            value_date=montrek_time(2024, 2, 3),
            field_tsc3_int=8,
            field_tsc3_str="what3",
        )
        self.user = MontrekUserFactory()

    def test_build_time_series_std_queryset(self):
        def make_assertions(test_query):
            test_query = test_query.order_by("created_at")
            self.assertEqual(test_query.count(), 6)
            test_obj_0 = test_query[0]
            self.assertEqual(test_obj_0.field_c1_str, "Hallo")
            self.assertEqual(test_obj_0.field_c1_bool, True)
            self.assertEqual(test_obj_0.field_tsc2_float, 1.0)
            self.assertEqual(test_obj_0.value_date, montrek_time(2024, 2, 5).date())
            self.assertEqual(test_obj_0.field_tsc3_int, None)
            self.assertEqual(test_obj_0.field_tsc3_str, None)
            test_obj_1 = test_query[2]
            self.assertEqual(test_obj_1.field_c1_str, "Test")
            self.assertEqual(test_obj_1.field_c1_bool, False)
            self.assertEqual(test_obj_1.field_tsc2_float, 2.5)
            self.assertEqual(test_obj_1.value_date, montrek_time(2024, 2, 6).date())
            self.assertEqual(test_obj_1.field_tsc3_int, 5)
            self.assertEqual(test_obj_1.field_tsc3_str, "what1")
            test_obj_2 = test_query[1]
            self.assertEqual(test_obj_2.field_c1_str, "Test")
            self.assertEqual(test_obj_2.field_c1_bool, False)
            self.assertEqual(test_obj_2.field_tsc2_float, 3.0)
            self.assertEqual(test_obj_2.value_date, montrek_time(2024, 2, 5).date())
            self.assertEqual(test_obj_2.field_tsc3_int, None)
            self.assertEqual(test_obj_2.field_tsc3_str, None)
            test_obj_3 = test_query[3]
            self.assertEqual(test_obj_3.field_c1_str, "DEFAULT")
            self.assertEqual(test_obj_3.field_c1_bool, False)
            self.assertEqual(test_obj_3.field_tsc2_float, 3.5)
            self.assertEqual(test_obj_3.value_date, montrek_time(2024, 2, 5).date())
            self.assertEqual(test_obj_3.field_tsc3_int, 7)
            self.assertEqual(test_obj_3.field_tsc3_str, "what2")
            test_obj_4 = test_query[4]
            self.assertEqual(test_obj_4.field_c1_str, "DEFAULT")
            self.assertEqual(test_obj_4.field_c1_bool, False)
            self.assertEqual(test_obj_4.field_tsc2_float, None)
            self.assertEqual(test_obj_4.value_date, None)
            self.assertEqual(test_obj_4.field_tsc3_int, None)
            self.assertEqual(test_obj_4.field_tsc3_str, None)

            test_obj_5 = test_query[5]
            self.assertEqual(test_obj_5.field_c1_str, None)
            self.assertEqual(test_obj_5.field_c1_bool, None)
            self.assertEqual(test_obj_5.field_tsc2_float, 0.0)  # Default is 0.0
            self.assertEqual(test_obj_5.value_date, montrek_time(2024, 2, 3).date())
            self.assertEqual(test_obj_5.field_tsc3_int, 8)
            self.assertEqual(test_obj_5.field_tsc3_str, "what3")

        repo = HubCRepository()
        # This query creates missing ts entries
        test_query = repo.std_queryset()
        make_assertions(test_query)
        # This catches all
        test_query = repo.std_queryset()
        make_assertions(test_query)

    def test_query_out_of_session_date(self):
        repo = HubCRepository(session_data={"end_date": datetime.datetime(2024, 1, 1)})
        test_query = repo.std_queryset()
        for query_element in test_query:
            self.assertEqual(query_element.value_date, None)
            self.assertEqual(query_element.field_tsc2_float, None)
            self.assertEqual(query_element.field_tsc3_int, None)
            self.assertEqual(query_element.field_tsc3_str, None)


class TestTimeSeriesQuerySetEmpty(TestCase):
    def test_empty_queryset(self):
        repo = HubCRepository()
        test_query = repo.std_queryset().filter(field_tsc3_int=42)
        self.assertEqual(test_query.count(), 0)


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

    def test_add_new_many_to_many_relation_via_data_frame(self):
        input_df = pd.DataFrame(
            {
                "field_b1_str": ["Hallo"],
                "field_b1_date": [montrek_time(2024, 3, 26)],
                "link_hub_b_hub_d": [[self.satd1.hub_entity, self.satd2.hub_entity]],
            }
        )
        repository_b = HubBRepository(session_data={"user_id": self.user.id})
        repository_b.create_objects_from_data_frame(input_df)
        new_sat_b = repository_b.std_queryset().last()
        links = new_sat_b.link_hub_b_hub_d.all()
        self.assertEqual(links.count(), 2)
        self.assertEqual(links[0], self.satd1.hub_entity)
        self.assertEqual(links[1], self.satd2.hub_entity)

    def test_update_existing_links(self):
        satd3 = me_factories.SatD1Factory(
            field_d1_str="dritter",
            field_d1_int=3,
        )
        satd4 = me_factories.SatD1Factory(
            field_d1_str="vierter",
            field_d1_int=4,
        )
        hub_entity_id = self.satb1.hub_entity_id

        # one existing, two new links
        input_data = {
            "hub_entity_id": hub_entity_id,
            "link_hub_b_hub_d": [
                self.satd1.hub_entity,
                satd3.hub_entity,
                satd4.hub_entity,
            ],
        }
        repository_b = HubBRepository(session_data={"user_id": self.user.id})
        repository_b.std_create_object(input_data)

        hub_b = repository_b.std_queryset().filter(id=hub_entity_id).first()

        links = me_models.LinkHubBHubD.objects.filter(hub_in=hub_b.id).all()
        continued = links.filter(hub_out=self.satd1.hub_entity).get()
        discontinued = links.filter(hub_out=self.satd2.hub_entity).get()
        new_1 = links.filter(hub_out=satd3.hub_entity).get()
        new_2 = links.filter(hub_out=satd4.hub_entity).get()

        self.assertEqual(hub_b.field_d1_str, "erster,zwoter,dritter,vierter")

        self.assertEqual(continued.state_date_start, MIN_DATE)
        self.assertEqual(continued.state_date_end, MAX_DATE)
        self.assertEqual(discontinued.state_date_start, MIN_DATE)
        self.assertEqual(discontinued.state_date_end, MAX_DATE)
        self.assertEqual(new_1.state_date_start, new_2.state_date_start)
        self.assertEqual(new_1.state_date_end, MAX_DATE)
        self.assertEqual(new_2.state_date_end, MAX_DATE)


class TestRepositoryProperties(TestCase):
    def test_static_satellites_fields(self):
        repo = HubCRepository()
        repo_c_static_satellite_fields = repo.get_static_satellite_field_names()
        expected_values = ["comment", "field_c1_str", "field_c1_bool", "hub_entity_id"]
        self.assertTrue(
            all(
                [
                    expected_value in repo_c_static_satellite_fields
                    for expected_value in expected_values
                ]
            )
        )

    def test_time_series_satellites_fields(self):
        repo = HubCRepository()
        repo_c_time_series_satellite_fields = (
            repo.get_time_series_satellite_field_names()
        )
        expected_values = [
            "field_tsc2_float",
            "field_tsc4_int",
            "field_tsc3_int",
            "field_tsc3_str",
            "comment",
            "value_date",
            "hub_entity_id",
        ]
        self.assertTrue(
            all(
                [
                    expected_value in repo_c_time_series_satellite_fields
                    for expected_value in expected_values
                ]
            )
        )


class TestGetHubsForValues(TestCase):
    def setUp(self):
        a1_str_values = ["a", "b", "c", "c", "", "x", "y", "z"]
        for hub_id, a1_str_value in enumerate(a1_str_values):
            hub = me_factories.HubAFactory(id=hub_id)
            me_factories.SatA1Factory(
                hub_entity=hub,
                state_date_start=montrek_time(2023, 7, 10),
                field_a1_str=a1_str_value,
            )

    def test_get_hubs_by_satellite_field_values(self):
        values = ["a", "b", "b", "c", "d", "e"]
        repository = HubARepository()
        actual = repository.get_hubs_by_satellite_field_values(
            values=values,
            by_repository_field="field_a1_str",
            raise_for_multiple_hubs=False,
            raise_for_unmapped_values=False,
        )
        actual_ids = [hub.id if hub else None for hub in actual]
        expected_ids = [0, 1, 1, 2, None, None]  # 2 is the first hub with value "c"
        self.assertEqual(actual_ids, expected_ids)

    def test_get_hubs_by_satellite_field_values_raises_error_for_multiple_hubs(self):
        values = ["a", "b", "c", "d", "e"]
        repository = HubARepository()
        with self.assertRaisesMessage(
            MontrekError, "Multiple hubs found for values (truncated): c"
        ):
            repository.get_hubs_by_satellite_field_values(
                values=values,
                by_repository_field="field_a1_str",
                raise_for_multiple_hubs=True,
                raise_for_unmapped_values=False,
            )

    def test_get_hubs_by_satellite_field_values_raises_error_for_unmapped_values(self):
        values = ["a", "b", "c", "d", "e"]
        repository = HubARepository()
        with self.assertRaisesMessage(
            MontrekError, "Cannot find hub for values (truncated): d, e"
        ):
            repository.get_hubs_by_satellite_field_values(
                values=values,
                by_repository_field="field_a1_str",
                raise_for_multiple_hubs=False,
                raise_for_unmapped_values=True,
            )

import datetime

import sys
import unittest
from django.db import models

import numpy as np
import pandas as pd
from baseclasses.errors.montrek_user_error import MontrekError
from baseclasses.tests.factories.montrek_factory_schemas import (
    ValueDateListFactory,
)
from baseclasses.utils import montrek_time
from django.core.exceptions import PermissionDenied
from django.test import TestCase, TransactionTestCase, tag
from django.utils import timezone
from user.tests.factories.montrek_user_factories import MontrekUserFactory

from montrek_example.models import example_models as me_models
from montrek_example.repositories.hub_a_repository import (
    HubAJsonRepository,
    HubARepository,
    HubARepository2,
    HubARepository3,
)
from montrek_example.repositories.hub_b_repository import (
    HubBRepository,
    HubBRepository2,
)
from montrek_example.repositories.hub_c_repository import (
    HubCRepository,
    HubCRepository2,
    HubCRepositoryCommonFields,
    HubCRepositoryLastTS,
    HubCRepositoryLast,
    HubCRepositoryOnlyStatic,
    HubCRepositorySumTS,
)
from montrek_example.repositories.hub_d_repository import (
    HubDRepository,
    HubDRepositoryReversedParentLink,
    HubDRepositoryTSReverseLink,
)
from montrek_example.repositories.hub_e_repository import (
    HubERepository,
)
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
                "value_date",
                "hub_entity_id",
                "created_at",
                "created_by",
                "comment",
                "field_a1_int",
                "field_a1_str",
                "field_a2_float",
                "field_a2_str",
                "field_b1_str",
                "field_b1_date",
                "dummy1",
                "dummy2",
            ],
        )

    def test_get_all_annotated_fields(self):
        repo = HubARepository()
        repo.add_linked_satellites_field_annotations(
            me_models.SatTSC2,
            me_models.LinkHubAHubC,
            ["field_tsc2_float"],
        )  # linked time series field
        repo.rename_field("field_a1_str", "my_field_a1_str")  # direct satellite field
        repo.rename_field("field_b1_str", "my_field_b1_str")  # linked field
        test_fields = repo.get_all_annotated_fields()
        self.assertEqual(
            test_fields,
            [
                "value_date",
                "hub_entity_id",
                "created_at",
                "created_by",
                "comment",
                "field_a1_int",
                "field_a2_float",
                "field_a2_str",
                "field_b1_date",
                "field_tsc2_float",
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
                "value_date",
                "hub_entity_id",
                "created_at",
                "created_by",
                "comment",
                "field_tsc2_float",
                "created_by__email",
                "field_tsc3_int",
                "field_tsc3_str",
                "field_tsc4_int",
                "field_c1_bool",
                "field_c1_str",
                "field_d1_str",
                "field_d1_int",
                "field_tsd2_float",
                "field_tsd2_int",
                "field_tsd2_float_agg",
                "field_tsd2_float_latest",
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
        self.assertEqual(me_models.AHubValueDate.objects.count(), 1)
        self.assertEqual(
            me_models.AHubValueDate.objects.first().hub, me_models.HubA.objects.first()
        )
        self.assertEqual(
            me_models.AHubValueDate.objects.first().value_date_list.value_date, None
        )

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
        self.assertEqual(me_models.AHubValueDate.objects.count(), 1)
        # Change the id of the first Satellite
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test_new",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
            }
        )
        # The receive should return the adjusted object
        a_object = HubARepository().receive().get()
        self.assertEqual(a_object.field_a1_str, "test_new")
        self.assertEqual(a_object.field_a1_int, 5)
        self.assertEqual(a_object.field_a2_str, "test2")
        self.assertEqual(a_object.field_a2_float, 6.0)
        self.assertEqual(a_object.created_by, self.user.email)

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
            HubARepository(session_data={"user_id": self.user.id}).receive().get()
        )
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test_new",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
                "hub_entity_id": a_object.hub_entity_id,
            }
        )
        # We should still have one Hub
        self.assertEqual(me_models.HubA.objects.count(), 1)

        # The receive should return the adjusted object
        b_object = HubARepository().receive().get()
        self.assertEqual(b_object.field_a1_str, "test_new")

    def test_std_create_object_update_all_satellites(self):
        repository = HubERepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "field_e1_str": "test",
                "field_e1_float": 2.5,
                "field_e2_str": "test2",
                "field_e2_int": 3,
            }
        )
        repository.std_create_object(
            {
                "field_e1_str": "test",
                "field_e1_float": 3.5,
                "field_e2_str": "test2",
                "field_e2_int": 3,
            }
        )
        # smoke test
        repository.receive().get()

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

    def test_update_satellite_and_raise_error_when_identifier_field_exists(self):
        existing_sat = me_factories.SatA1Factory(
            field_a1_int=3, field_a1_str="existing"
        )
        me_factories.SatA2Factory(
            field_a2_float=4.0,
            field_a2_str="existing2",
            hub_entity=existing_sat.hub_entity,
        )
        repository = HubARepository(session_data={"user_id": self.user.id})
        test_hub = repository.create_by_dict(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
            }
        )
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 2)
        new_obj = test_query.get(field_a1_str="test")
        self.assertEqual(new_obj.field_a1_int, 5)
        ## Change test_hub to existing_sat identifier field
        with self.assertRaises(MontrekError):
            repository.create_by_dict(
                {
                    "field_a1_int": 5,
                    "field_a1_str": "existing",
                    "field_a2_float": 6.0,
                    "field_a2_str": "existing2",
                    "hub_entity_id": test_hub.id,
                }
            )


class TestMontrekCreateTimeSeriesObject(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()

    def test_create_object_ts_update(self):
        repository = HubCRepository(session_data={"user_id": self.user.id})
        existing_hub = repository.std_create_object(
            {
                "field_tsc2_float": 5.0,
                "value_date": "2024-11-21",
            }
        )
        self.assertEqual(me_models.HubC.objects.count(), 1)
        self.assertEqual(me_models.SatC1.objects.count(), 0)
        self.assertEqual(me_models.SatTSC2.objects.count(), 1)
        self.assertEqual(me_models.SatTSC3.objects.count(), 0)
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 1)
        self.assertEqual(test_query[0].field_tsc2_float, 5.0)
        repository.std_create_object(
            {
                "field_tsc2_float": 5.0,
                "hub_entity_id": existing_hub.id,
                "value_date": "2024-11-21",
            }
        )
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 1)
        self.assertEqual(test_query[0].field_tsc2_float, 5.0)
        repository.std_create_object(
            {
                "field_tsc2_float": 4.0,
                "hub_entity_id": existing_hub.id,
                "value_date": "2024-11-21",
            }
        )
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 1)
        self.assertEqual(test_query[0].field_tsc2_float, 4.0)

    def test_create_ts_satellite_with_given_hub(self):
        hub = me_factories.HubCFactory()
        repository = HubCRepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "hub_entity_id": hub.id,
                "field_c1_str": "test",
                "field_tsc2_float": 6.0,
                "value_date": "2023-07-08",
            }
        )
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 1)
        queried_object = test_query.get()
        self.assertEqual(queried_object.field_c1_str, "test")
        self.assertEqual(queried_object.field_tsc2_float, 6.0)
        self.assertEqual(queried_object.hub, hub)
        self.assertEqual(queried_object.value_date, montrek_time(2023, 7, 8).date())

    def test_create_ts_satellite_with_given_static_id(self):
        sat = me_factories.SatC1Factory(field_c1_str="test")
        repository = HubCRepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "field_c1_str": "test",
                "field_tsc2_float": 6.0,
                "value_date": "2023-07-08",
            }
        )
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 1)
        queried_object = test_query.get()
        self.assertEqual(queried_object.field_c1_str, "test")
        self.assertEqual(queried_object.field_tsc2_float, 6.0)
        self.assertEqual(queried_object.hub, sat.hub_entity)
        self.assertEqual(queried_object.value_date, montrek_time(2023, 7, 8).date())

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
        queried_object = repository.receive().get()
        self.assertEqual(queried_object.field_a2_float, 0.0)


class TestMontrekCreateObjectDataFrame(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()

    def test_create__empty_data_frame(self):
        repository = HubCRepository(session_data={"user_id": self.user.id})
        data_frame = pd.DataFrame()
        repository.create_objects_from_data_frame(data_frame)
        self.assertEqual(me_models.HubC.objects.count(), 0)

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

    def test_create_objects_from_data_frame_return_hubs(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        data_frame = pd.DataFrame(
            {
                "field_a1_int": [5, 6],
                "field_a1_str": ["test", "test2"],
                "field_a2_float": [6.0, 7.0],
                "field_a2_str": ["test2", "test3"],
            }
        )
        produced_hubs = repository.create_objects_from_data_frame(data_frame)
        self.assertEqual(len(produced_hubs), 2)
        produced_hubs = repository.create_objects_from_data_frame(data_frame)
        self.assertEqual(len(produced_hubs), 0)
        data_frame = pd.DataFrame(
            {
                "field_a1_int": [5, 7],
                "field_a1_str": ["test", "test2"],
                "field_a2_float": [6.0, 7.0],
                "field_a2_str": ["test2", "test3"],
            }
        )
        produced_hubs = repository.create_objects_from_data_frame(data_frame)
        self.assertEqual(len(produced_hubs), 1)

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
        test_query = repository.receive()
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
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 2)
        self.assertEqual(test_query[0].field_a1_int, 5)
        self.assertEqual(repository.messages[0].message, "1 empty rows not uploaded!")

    def test_create_objects_from_data_frame_fields_nan(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        data_frame = pd.DataFrame(
            {
                "field_a1_int": [5, 6, 7],
                "field_a1_str": ["test", "test2", "test3"],
                "field_a2_float": [6.0, 7.0, np.nan],
                "field_a2_str": ["test2", "test3", "test4"],
            }
        )
        repository.create_objects_from_data_frame(data_frame)
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 3)

    def test_create_objects_from_data_frame_missing_primary_satellite_identifier_column(
        self,
    ):
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.receive()
        # A missing field_a1_str column should hot raise an error.
        data_frame = pd.DataFrame(
            {
                "field_a2_float": [6.0, 7.0, 8.0],
                "field_a2_str": ["test2", "test3", "test4"],
            }
        )
        repository.create_objects_from_data_frame(data_frame)
        queryset = repository.receive()
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
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 3)
        self.assertEqual(me_models.HubC.objects.count(), 2)
        self.assertEqual(me_models.SatC1.objects.count(), 2)

    def test_create_objects_from_data_frame__static_and_ts_data__new(self):
        repository = HubCRepository(session_data={"user_id": self.user.id})
        data_frame = pd.DataFrame(
            {
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
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 3)
        self.assertEqual(me_models.HubC.objects.count(), 2)
        self.assertEqual(me_models.SatC1.objects.count(), 2)

    def test_create_objects_from_data_frame__ts_data_update(self):
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
        data_frame = pd.DataFrame(
            {
                "hub_entity_id": [hub1.id, hub1.id, hub2.id],
                "value_date": ["2024-08-01", "2024-08-02", "2024-08-02"],
                "field_tsc2_float": [5.0, 6.0, 8.0],
            }
        )
        repository.create_objects_from_data_frame(data_frame)
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 3)
        self.assertEqual(me_models.HubC.objects.count(), 2)
        self.assertEqual(me_models.SatC1.objects.count(), 2)
        self.assertEqual(test_query[0].field_tsc2_float, 5.0)

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
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 3)

    def test_drop_duplicates_separate_satellites(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        data_frame = pd.DataFrame(
            {
                "field_a1_int": [5, 6, 7],
                "field_a1_str": ["test", "test2", "test3"],
                "field_a2_float": [6.0, 7.0, 8.0],
                "field_a2_str": ["test2", "test2", "test4"],
            }
        )
        self.assertRaisesMessage(
            ValueError,
            "Duplicated entries found for SatA2 with fields ['field_a2_str']\n",
            repository.create_objects_from_data_frame,
            data_frame,
        )


class TestMontrekCreateObjectLinks(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()

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
        queried_object = repository.receive().get()
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
        queried_object = repository.receive().get()
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
        queried_object = repository.receive().get()
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
        queried_object = repository.receive().get()
        self.assertEqual(queried_object.field_b1_str, sat_b_1.field_b1_str)

    def test_update_one_to_many_link(self):
        sat_c_1 = me_factories.SatC1Factory(
            field_c1_str="test1",
        )
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
                "link_hub_a_hub_c": sat_c_1.hub_entity,
            }
        )
        self.assertEqual(me_models.LinkHubAHubC.objects.count(), 1)
        self.assertEqual(
            me_models.LinkHubAHubC.objects.first().state_date_end, MAX_DATE
        )
        # Check that link start date is set to creation date (which is for sure less than 5 minutes ago)
        self.assertTrue(
            me_models.LinkHubAHubC.objects.first().state_date_start
            > timezone.now() - datetime.timedelta(minutes=5)
        )
        test_repository = HubARepository2({})
        test_a_object = test_repository.receive().get()
        self.assertEqual(test_a_object.field_c1_str, "test1")
        sat_c_2 = me_factories.SatC1Factory(
            field_c1_str="test2",
        )
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
                "link_hub_a_hub_c": sat_c_2.hub_entity,
            }
        )
        self.assertEqual(me_models.LinkHubAHubC.objects.count(), 2)
        old_link = me_models.LinkHubAHubC.objects.first()
        new_link = me_models.LinkHubAHubC.objects.last()
        self.assertEqual(new_link.state_date_end, MAX_DATE)
        self.assertEqual(old_link.state_date_end, new_link.state_date_start)
        test_repository = HubARepository2({})
        test_a_object = test_repository.receive().get()
        self.assertEqual(test_a_object.field_c1_str, "test2")


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
        deletion_object = repository.receive().get().hub
        repository.delete(deletion_object)
        self.assertEqual(me_models.SatA1.objects.count(), 1)
        self.assertLess(me_models.SatA1.objects.first().state_date_end, timezone.now())
        self.assertEqual(me_models.HubA.objects.count(), 1)
        self.assertEqual(len(repository.receive()), 0)

    def test_reintroduce_deleted_object(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.std_create_object({"field_a1_int": 5, "field_a1_str": "test"})
        deletion_object = repository.receive().get().hub
        repository.delete(deletion_object)
        repository.std_create_object({"field_a1_int": 5, "field_a1_str": "test"})
        self.assertEqual(me_models.SatA1.objects.count(), 2)
        self.assertEqual(me_models.HubA.objects.count(), 2)
        self.assertEqual(len(repository.receive()), 1)


class TestMontrekRepositoryLinks(TestCase):
    def setUp(self):
        self.huba1 = me_factories.HubAFactory()
        self.huba2 = me_factories.HubAFactory()
        me_factories.AHubValueDateFactory(hub=self.huba2, value_date=None)
        hubc1 = me_factories.HubCFactory()
        hubc2 = me_factories.HubCFactory()

        me_factories.SatA1Factory(
            hub_entity=self.huba1,
            field_a1_int=5,
        )
        me_factories.LinkHubAHubCFactory(
            hub_in=self.huba1,
            hub_out=hubc1,
        )
        me_factories.LinkHubAHubCFactory(
            hub_in=self.huba2,
            hub_out=hubc1,
            state_date_end=montrek_time(2023, 7, 12),
        )
        me_factories.LinkHubAHubCFactory(
            hub_in=self.huba2,
            hub_out=hubc2,
            state_date_start=montrek_time(2023, 7, 12),
        )
        me_factories.SatC1Factory(
            hub_entity=hubc1,
            state_date_end=montrek_time(2023, 7, 10),
            field_c1_str="First",
        )
        me_factories.SatC1Factory(
            hub_entity=hubc1,
            state_date_start=montrek_time(2023, 7, 10),
            field_c1_str="Second",
        )
        me_factories.SatC1Factory(
            hub_entity=hubc2,
            field_c1_str="Third",
        )

    def test_many_to_one_link(self):
        repository = HubARepository2()
        repository.reference_date = montrek_time(2023, 7, 8)
        queryset = repository.receive()

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_c1_str, "First")
        self.assertEqual(queryset[1].field_c1_str, "First")

        repository.reference_date = montrek_time(2023, 7, 10)
        queryset = repository.receive()

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_c1_str, "Second")
        self.assertEqual(queryset[1].field_c1_str, "Second")

        repository.reference_date = montrek_time(2023, 7, 12)
        queryset = repository.receive()

        self.assertEqual(queryset.count(), 2)
        qs_1 = queryset.get(hub_entity_id=self.huba1.id)
        qs_2 = queryset.get(hub_entity_id=self.huba2.id)
        self.assertEqual(qs_2.field_c1_str, "Third")
        self.assertEqual(qs_1.field_c1_str, "Second")

    def test_link_reversed(self):
        repository = HubCRepository2()
        repository.reference_date = montrek_time(2023, 7, 8)
        queryset = repository.receive()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_a1_int, "5")
        self.assertEqual(queryset[1].field_a1_int, None)
        repository.reference_date = montrek_time(2023, 7, 15)
        queryset = repository.receive()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_a1_int, "5")
        self.assertEqual(queryset[1].field_a1_int, None)

    def test_link_reversed__session_data(self):
        repository = HubCRepository2({"reference_date": "2023-07-08"})
        queryset = repository.receive()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_a1_int, "5")
        self.assertEqual(queryset[1].field_a1_int, None)
        repository = HubCRepository2({"reference_date": ["2023-07-15"]})
        queryset = repository.receive()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_a1_int, "5")
        self.assertEqual(queryset[1].field_a1_int, None)

    def test_link_reversed_ts(self):
        sat_tsc2 = me_factories.SatTSC2Factory(
            field_tsc2_float=2.5, value_date="2024-11-19"
        )
        d_hub = me_factories.DHubValueDateFactory(value_date="2024-11-19").hub
        sat_tsc2.hub_value_date.hub.link_hub_c_hub_d.add(d_hub)
        queryset = HubDRepositoryTSReverseLink({}).receive()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].field_tsc2_float, "2.5")

    def test_link_with_parent_links(self):
        hubc = me_factories.HubCFactory()
        hubd = me_factories.HubDFactory()
        me_factories.SatD1Factory.create(hub_entity=hubd, field_d1_str="Test")
        me_factories.LinkHubCHubDFactory(hub_in=hubc, hub_out=hubd)
        me_factories.LinkHubAHubCFactory(hub_in=self.huba1, hub_out=hubc)
        repository = HubARepository3()
        queryset = repository.receive()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_d1_str, "Test")

    def test_link_reversed_with_parent_links(self):
        hubc = me_factories.HubCFactory()
        hubd = me_factories.HubDFactory()
        me_factories.SatA1Factory.create(hub_entity=self.huba1, field_a1_str="Test")
        me_factories.LinkHubCHubDFactory(hub_in=hubc, hub_out=hubd)
        me_factories.LinkHubAHubCFactory(hub_in=self.huba1, hub_out=hubc)
        repository = HubDRepositoryReversedParentLink()
        queryset = repository.receive()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().field_a1_str, "Test")


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
        self.assertEqual(link_1.state_date_end, link_2.state_date_start)
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

    def test_aggreagte_multiples_sum(self):
        hub_c = me_factories.HubCFactory()
        sat_d1 = me_factories.SatD1Factory(field_d1_int=5)
        sat_d2 = me_factories.SatD1Factory(field_d1_int=6)
        sat_d3 = me_factories.SatD1Factory(field_d1_int=7)
        hub_c.link_hub_c_hub_d.add(sat_d1.hub_entity)
        hub_c.link_hub_c_hub_d.add(sat_d2.hub_entity)
        hub_c.link_hub_c_hub_d.add(sat_d3.hub_entity)
        test_query = HubCRepository().receive()
        self.assertEqual(test_query.last().field_d1_int, 11)


class TestCreateDataWithLinks(TestCase):
    def setUp(self) -> None:
        user = MontrekUserFactory()
        self.session_data = {"user_id": user.id}

    def test_create_data_with_one_link(self):
        self.hub_vd1 = me_factories.DHubValueDateFactory()
        # self.hub_vd2 = me_factories.DHubValueDateFactory()
        me_factories.SatD1Factory.create(
            field_d1_str="test1",
            hub_entity=self.hub_vd1.hub,
        )

        # me_factories.SatD1Factory.create(
        #     field_d1_str="test2",
        #     hub_entity=self.hub_vd2.hub,
        # )

        creation_data = {
            "field_b1_str": "test",
            "field_b1_date": "2024-02-17",
            "field_b2_str": "test2",
            "field_b2_choice": "CHOICE2",
            "link_hub_b_hub_d": self.hub_vd1,
        }
        repo = HubBRepository(session_data=self.session_data)
        repo.std_create_object(creation_data)
        queryset = repo.receive()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].field_d1_str, "test1")

    def test_create_data_with_two_link(self):
        self.hub_vd1 = me_factories.DHubValueDateFactory()
        self.hub_vd2 = me_factories.DHubValueDateFactory()
        me_factories.SatD1Factory.create(
            field_d1_str="test1",
            hub_entity=self.hub_vd1.hub,
        )

        me_factories.SatD1Factory.create(
            field_d1_str="test2",
            hub_entity=self.hub_vd2.hub,
        )

        creation_data = {
            "field_b1_str": "test",
            "field_b1_date": "2024-02-17",
            "field_b2_str": "test2",
            "field_b2_choice": "CHOICE2",
            "link_hub_b_hub_d": [self.hub_vd1, self.hub_vd2],
        }
        repo = HubBRepository(session_data=self.session_data)
        repo.std_create_object(creation_data)
        queryset = repo.receive()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].field_d1_str, "test1,test2")


class TestTimeSeries(TestCase):
    def setUp(self) -> None:
        ts_satellite_c1 = me_factories.SatC1Factory.create(
            field_c1_str="Hallo",
            field_c1_bool=True,
        )

        me_factories.SatTSC2Factory.create(
            hub_value_date__hub=ts_satellite_c1.hub_entity,
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
        object_1 = queryset.get(field_tsc2_float=1.0)
        self.assertEqual(object_1.value_date, montrek_time(2024, 2, 5).date())
        object_2 = queryset.get(field_tsc2_float=2.0)
        self.assertEqual(object_2.value_date, montrek_time(2024, 2, 5).date())
        self.assertEqual(object_1.state_date_end, object_2.state_date_start)

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
            sat_c.hub_value_date.hub.link_hub_c_hub_d.add(sat_d.hub_value_date.hub)
        repository = HubCRepository(session_data={"user_id": self.user.id})
        test_query = repository.receive().filter(value_date__in=value_dates)
        self.assertEqual(test_query.count(), 2)
        result_1 = test_query.get(value_date=value_dates[0])
        result_2 = test_query.get(value_date=value_dates[1])
        self.assertEqual(result_1.field_tsc2_float, 0.0)
        self.assertEqual(result_1.field_tsd2_float, "0")
        self.assertEqual(result_1.field_tsd2_int, "0")
        self.assertEqual(result_2.field_tsc2_float, 0.1)
        self.assertEqual(result_2.field_tsd2_float, "0.2")
        self.assertEqual(result_2.field_tsd2_int, "1")

    def test_satellite_filter_in_time_series(self):
        value_dates = [montrek_time(2024, 9, 18), montrek_time(2024, 9, 19)]
        for i, value_date in enumerate(value_dates):
            sat_c = me_factories.SatTSC2Factory.create(
                field_tsc2_float=i * -0.1,
                value_date=value_date,
            )
            sat_d = me_factories.SatTSD2Factory.create(
                field_tsd2_float=i * -0.2,
                field_tsd2_int=i,
                value_date=value_date,
            )
            sat_c.hub_value_date.hub.link_hub_c_hub_d.add(sat_d.hub_value_date.hub)

        repository = HubCRepository(session_data={"user_id": self.user.id})
        test_query = repository.receive().filter(value_date__in=value_dates)
        self.assertEqual(test_query.count(), 2)
        result_1 = test_query.get(value_date=value_dates[0])
        result_2 = test_query.get(value_date=value_dates[1])
        self.assertEqual(result_1.field_tsd2_float, "0")
        self.assertEqual(result_2.field_tsd2_float, None)

    def test_time_series_link_to_time_series_update(self):
        value_date = montrek_time(2024, 9, 18)
        sat_d1 = me_factories.SatTSD2Factory.create(
            field_tsd2_float=0.2,
            field_tsd2_int=2,
            value_date=value_date,
        )
        sat_d2 = me_factories.SatTSD2Factory.create(
            field_tsd2_float=0.3,
            field_tsd2_int=3,
            value_date=value_date,
        )
        repository = HubCRepository(session_data={"user_id": self.user.id})
        repository.create_by_dict(
            {
                "field_tsc2_float": 0.1,
                "value_date": value_date,
                "link_hub_c_hub_d": sat_d1.hub_value_date.hub,
            }
        )
        repository.create_by_dict(
            {
                "field_tsc2_float": 0.2,
                "value_date": value_date,
                "link_hub_c_hub_d": sat_d2.hub_value_date.hub,
            }
        )
        test_query = repository.receive().filter(value_date=value_date)
        created_obj = test_query.first()
        self.assertEqual(float(created_obj.field_tsd2_float), 0.2)
        self.assertEqual(int(created_obj.field_tsd2_int), 2)
        repository.create_by_dict(
            {
                "link_hub_c_hub_d": sat_d2.hub_value_date.hub,
                "hub_entity_id": created_obj.hub.pk,
            }
        )
        test_query = repository.receive().filter(value_date=value_date)
        self.assertEqual(test_query.count(), 2)
        test_obj = test_query.first()
        self.assertEqual(float(test_obj.field_tsd2_float), 0.3)
        self.assertEqual(int(test_obj.field_tsd2_int), 3)
        self.assertEqual(float(test_obj.field_tsc2_float), 0.1)
        test_obj = test_query.last()
        self.assertEqual(float(test_obj.field_tsd2_float), 0.3)
        self.assertEqual(int(test_obj.field_tsd2_int), 3)
        self.assertEqual(float(test_obj.field_tsc2_float), 0.2)

    def test_time_series_link_to_time_series_close_hub(self):
        value_date = montrek_time(2024, 9, 18)
        sat_d1 = me_factories.SatTSD2Factory.create(
            field_tsd2_float=0.2,
            field_tsd2_int=2,
            value_date=value_date,
        )
        repository = HubCRepository(session_data={"user_id": self.user.id})
        repository.create_by_dict(
            {
                "field_tsc2_float": 0.1,
                "value_date": value_date,
                "link_hub_c_hub_d": sat_d1.hub_value_date.hub,
            }
        )
        test_query = repository.receive().filter(value_date=value_date)
        created_obj = test_query.first()
        self.assertEqual(float(created_obj.field_tsd2_float), 0.2)
        self.assertEqual(int(created_obj.field_tsd2_int), 2)
        self.assertEqual(float(created_obj.field_tsc2_float), 0.1)
        sat_d1.hub_value_date.hub.state_date_end = montrek_time(2024, 10, 1)
        sat_d1.hub_value_date.hub.save()
        test_query = repository.receive().filter(value_date=value_date)
        created_obj = test_query.first()
        self.assertEqual(created_obj.field_tsd2_float, None)
        self.assertEqual(created_obj.field_tsd2_int, None)
        self.assertEqual(float(created_obj.field_tsc2_float), 0.1)


class TestTimeSeriesRepositoryEmpty(TestCase):
    def test_empty_time_series(self):
        repository = HubCRepository()
        queryset = repository.receive()
        self.assertEqual(queryset.count(), 0)
        queryset.filter(field_tsc2_float__isnull=True)

    def test_first_container_empty(self):
        repository = HubCRepository()
        me_factories.SatTSC3Factory.create(
            field_tsc3_str="Test",
            value_date=montrek_time(2024, 2, 5),
            field_tsc3_int=5,
        )
        qs = repository.receive()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].field_tsc3_str, "Test")
        self.assertEqual(qs[0].field_tsc3_int, 5)


class TestTimeSeriesQuerySet(TestCase):
    def setUp(self) -> None:
        ts_satellite_c1 = me_factories.SatC1Factory.create(
            field_c1_str="Hallo",
            field_c1_bool=True,
        )
        self.ts_fact0 = me_factories.SatTSC2Factory.create(
            hub_value_date__hub=ts_satellite_c1.hub_entity,
            field_tsc2_float=4.0,
            value_date=montrek_time(2024, 2, 5),
        )
        static_sats = me_factories.SatC1Factory.create_batch(3)
        self.ts_fact1 = me_factories.SatTSC2Factory.create(
            hub_value_date__hub=static_sats[0].hub_entity,
            field_tsc2_float=1.0,
            value_date=montrek_time(2024, 2, 5),
            state_date_end=montrek_time(2024, 7, 6),
        )
        self.ts_fact2 = me_factories.SatTSC2Factory.create(
            hub_value_date=self.ts_fact1.hub_value_date,
            field_tsc2_float=3.0,
            state_date_start=montrek_time(2024, 7, 6),
        )
        me_factories.SatTSC2Factory.create(
            hub_value_date__hub=static_sats[0].hub_entity,
            value_date=montrek_time(2024, 2, 6),
        )
        me_factories.SatTSC2Factory.create(
            hub_value_date__hub=static_sats[1].hub_entity,
            value_date=montrek_time(2024, 2, 5),
        )
        self.user = MontrekUserFactory()

    def test_build_time_series_queryset(self):
        repo = HubCRepository()
        test_query = repo.receive()
        self.assertEqual(test_query.count(), 5)
        qs_1 = test_query.get(pk=self.ts_fact0.hub_value_date.id)
        qs_2 = test_query.get(pk=self.ts_fact1.hub_value_date.id)
        self.assertEqual(qs_1.field_tsc2_float, self.ts_fact0.field_tsc2_float)
        self.assertEqual(qs_2.field_tsc2_float, self.ts_fact2.field_tsc2_float)

    def test_build_time_series_queryset__reference_date_filter(self):
        repo = HubCRepository()
        repo.reference_date = montrek_time(2024, 7, 1)
        test_query = repo.receive()
        self.assertEqual(test_query.count(), 5)
        qs_1 = test_query.get(pk=self.ts_fact0.hub_value_date.id)
        qs_2 = test_query.get(pk=self.ts_fact1.hub_value_date.id)
        self.assertEqual(qs_1.field_tsc2_float, self.ts_fact0.field_tsc2_float)
        self.assertEqual(qs_2.field_tsc2_float, self.ts_fact1.field_tsc2_float)

    def test_build_time_series_queryset__reference_date_filter__session_data(self):
        repo = HubCRepository({"reference_date": montrek_time(2024, 7, 1)})
        test_query = repo.receive()
        self.assertEqual(test_query.count(), 5)
        qs_1 = test_query.get(pk=self.ts_fact0.hub_value_date.id)
        qs_2 = test_query.get(pk=self.ts_fact1.hub_value_date.id)
        self.assertEqual(qs_1.field_tsc2_float, self.ts_fact0.field_tsc2_float)
        self.assertEqual(qs_2.field_tsc2_float, self.ts_fact1.field_tsc2_float)

    def test_build_time_series_queryset__session_dates(self):
        for end_date, expected_count in [
            (datetime.datetime(2024, 2, 1), 1),
            (datetime.datetime(2024, 2, 5), 4),
            (datetime.datetime(2024, 2, 6), 5),
            (datetime.datetime(2024, 2, 7), 5),
        ]:
            repo = HubCRepository(session_data={"end_date": end_date})
            test_query = repo.receive()
            self.assertEqual(test_query.count(), expected_count)
        for start_date, expected_count in [
            (datetime.datetime(2024, 2, 1), 5),
            (datetime.datetime(2024, 2, 5), 5),
            (datetime.datetime(2024, 2, 6), 2),
            (datetime.datetime(2024, 2, 7), 1),
        ]:
            repo = HubCRepository(session_data={"start_date": start_date})
            test_query = repo.receive()
            self.assertEqual(test_query.count(), expected_count)


class TestTimeSeriesStdQueryset(TestCase):
    def setUp(self) -> None:
        ts_satellite_c1 = me_factories.SatC1Factory.create(
            field_c1_str="Hallo",
            field_c1_bool=True,
        )
        me_factories.SatTSC2Factory.create(
            hub_value_date__hub=ts_satellite_c1.hub_entity,
            field_tsc2_float=1.0,
            value_date=montrek_time(2024, 2, 5),
        )
        static_sats = me_factories.SatC1Factory.create_batch(3)
        static_sats[0].field_c1_str = "Test"
        static_sats[0].save()
        ts_sat_0 = me_factories.SatTSC2Factory.create(
            hub_value_date__hub=static_sats[0].hub_entity,
            field_tsc2_float=2.0,
            value_date=montrek_time(2024, 2, 5),
            state_date_end=montrek_time(2024, 7, 6),
        )
        me_factories.SatTSC2Factory.create(
            hub_value_date=ts_sat_0.hub_value_date,
            field_tsc2_float=3.0,
            state_date_start=montrek_time(2024, 7, 6),
        )
        ts_sat_1 = me_factories.SatTSC2Factory.create(
            hub_value_date__hub=static_sats[0].hub_entity,
            value_date=montrek_time(2024, 2, 6),
            field_tsc2_float=2.5,
        )
        ts_sat_2 = me_factories.SatTSC2Factory.create(
            hub_value_date__hub=static_sats[1].hub_entity,
            value_date=montrek_time(2024, 2, 5),
            field_tsc2_float=3.5,
        )
        me_factories.SatTSC3Factory.create(
            hub_value_date=ts_sat_1.hub_value_date,
            field_tsc3_int=5,
            field_tsc3_str="what1",
        )
        me_factories.SatTSC3Factory.create(
            hub_value_date=ts_sat_2.hub_value_date,
            field_tsc3_int=7,
            field_tsc3_str="what2",
        )
        me_factories.SatTSC3Factory.create(
            value_date=montrek_time(2024, 2, 3),
            field_tsc3_int=8,
            field_tsc3_str="what3",
        )
        self.user = MontrekUserFactory()

    def test_build_time_series_receive(self):
        def make_assertions(test_query):
            self.assertEqual(test_query.count(), 6)
            test_obj_1 = test_query.get(
                field_c1_str="Test", value_date=montrek_time(2024, 2, 6).date()
            )
            self.assertEqual(test_obj_1.field_c1_bool, False)
            self.assertEqual(test_obj_1.field_tsc2_float, 2.5)
            self.assertEqual(test_obj_1.field_tsc3_int, 5)
            self.assertEqual(test_obj_1.field_tsc3_str, "what1")
            test_obj_0 = test_query.get(
                field_c1_str="Hallo", value_date=montrek_time(2024, 2, 5).date()
            )
            self.assertEqual(test_obj_0.field_c1_bool, True)
            self.assertEqual(test_obj_0.field_tsc2_float, 1.0)
            self.assertEqual(test_obj_0.field_tsc3_int, None)
            self.assertEqual(test_obj_0.field_tsc3_str, None)
            test_obj_2 = test_query.get(
                field_c1_str="Test", value_date=montrek_time(2024, 2, 5).date()
            )
            self.assertEqual(test_obj_2.field_c1_bool, False)
            self.assertEqual(test_obj_2.field_tsc2_float, 3.0)
            self.assertEqual(test_obj_2.field_tsc3_int, None)
            self.assertEqual(test_obj_2.field_tsc3_str, None)
            test_obj_3 = test_query.get(
                field_c1_str="DEFAULT", value_date=montrek_time(2024, 2, 5).date()
            )
            self.assertEqual(test_obj_3.field_c1_bool, False)
            self.assertEqual(test_obj_3.field_tsc2_float, 3.5)
            self.assertEqual(test_obj_3.field_tsc3_int, 7)
            self.assertEqual(test_obj_3.field_tsc3_str, "what2")
            test_obj_4 = test_query.get(field_c1_str="DEFAULT", value_date=None)
            self.assertEqual(test_obj_4.field_c1_bool, False)
            self.assertEqual(test_obj_4.field_tsc2_float, None)
            self.assertEqual(test_obj_4.field_tsc3_int, None)
            self.assertEqual(test_obj_4.field_tsc3_str, None)
            test_obj_5 = test_query.get(
                field_c1_str=None, value_date=montrek_time(2024, 2, 3).date()
            )
            self.assertEqual(test_obj_5.field_c1_bool, None)
            self.assertEqual(test_obj_5.field_tsc2_float, None)  # Default is 0.0
            self.assertEqual(test_obj_5.field_tsc3_int, 8)
            self.assertEqual(test_obj_5.field_tsc3_str, "what3")

        repo = HubCRepository()
        # This query creates missing ts entries
        test_query = repo.receive()
        make_assertions(test_query)
        # This catches all
        test_query = repo.receive()
        make_assertions(test_query)

    def test_query_out_of_session_date(self):
        repo = HubCRepository(session_data={"end_date": datetime.datetime(2024, 1, 1)})
        test_query = repo.receive()
        for query_element in test_query:
            self.assertEqual(query_element.value_date, None)
            self.assertEqual(query_element.field_tsc2_float, None)
            self.assertEqual(query_element.field_tsc3_int, None)
            self.assertEqual(query_element.field_tsc3_str, None)


class TestTSRepoLatestTS(TestCase):
    def setUp(self):
        self.sat1 = me_factories.SatTSC2Factory.create(
            value_date="2024-11-15", field_tsc2_float=1.0
        )
        sat2 = me_factories.SatTSC2Factory.create(
            value_date="2024-11-15", field_tsc2_float=2.0
        )
        hub_vd1 = me_factories.CHubValueDateFactory.create(
            hub=self.sat1.hub_value_date.hub,
            value_date_list=me_factories.ValueDateListFactory.create(
                value_date="2024-11-16"
            ),
        )
        hub_vd2 = me_factories.CHubValueDateFactory.create(
            hub=sat2.hub_value_date.hub,
            value_date_list=hub_vd1.value_date_list,
        )
        me_factories.SatTSC2Factory.create(
            hub_value_date=hub_vd1,
            field_tsc2_float=3.0,
        )
        me_factories.SatTSC2Factory.create(
            hub_value_date=hub_vd2,
            field_tsc2_float=4.0,
        )
        me_factories.SatC1Factory.create(
            field_c1_str="Hallo",
            hub_entity=self.sat1.hub_value_date.hub,
        )
        me_factories.SatC1Factory.create(
            field_c1_str="Bonjour",
            hub_entity=sat2.hub_value_date.hub,
        )
        me_factories.SatC1Factory.create(
            field_c1_str="Hola",
        )

    def test_last_ts_repo(self):
        repo = HubCRepositoryLastTS()
        test_query = repo.receive()
        self.assertEqual(test_query.count(), 3)
        qs1 = test_query.get(field_c1_str="Hallo")
        self.assertEqual(qs1.field_tsc2_float, 3.0)
        self.assertEqual(qs1.value_date, montrek_time(2024, 11, 16).date())
        qs2 = test_query.get(field_c1_str="Bonjour")
        self.assertEqual(qs2.field_tsc2_float, 4.0)
        self.assertEqual(qs2.value_date, montrek_time(2024, 11, 16).date())
        qs3 = test_query.get(field_c1_str="Hola")
        self.assertEqual(qs3.field_tsc2_float, None)
        self.assertEqual(qs3.value_date, None)

    def test_ts_sum_repo(self):
        hub_vd1 = me_factories.CHubValueDateFactory.create(
            hub=self.sat1.hub_value_date.hub,
            value_date_list=me_factories.ValueDateListFactory.create(
                value_date="2024-11-17"
            ),
        )
        me_factories.SatTSC2Factory.create(
            hub_value_date=hub_vd1,
            field_tsc2_float=5.0,
        )
        repo = HubCRepositorySumTS()
        test_query = repo.receive()
        self.assertEqual(test_query.count(), 3)
        qs1 = test_query.get(field_c1_str="Bonjour")
        self.assertEqual(qs1.agg_field_tsc2_float, 6.0)
        qs2 = test_query.get(field_c1_str="Hallo")
        self.assertEqual(qs2.agg_field_tsc2_float, 9.0)

    def test_only_statics(self):
        repo = HubCRepositoryOnlyStatic()
        test_query = repo.receive()
        self.assertEqual(test_query.count(), 3)
        c1_vals = [qs.field_c1_str for qs in test_query]
        c1_vals.sort()
        self.assertEqual(c1_vals, ["Bonjour", "Hallo", "Hola"])


class TestStaticAggFuncs(TestCase):
    def setUp(self) -> None:
        sat_d1_1 = me_factories.SatD1Factory(field_d1_int=2)
        sat_d1_2 = me_factories.SatD1Factory(field_d1_int=3)
        sat_c1 = me_factories.SatC1Factory()
        sat_c1.hub_entity.link_hub_c_hub_d.add(sat_d1_1.hub_entity)
        sat_c1.hub_entity.link_hub_c_hub_d.add(sat_d1_2.hub_entity)

    def test_latest_entry(self):
        repo = HubCRepositoryLast()
        test_query = repo.receive()
        self.assertEqual(test_query.count(), 1)
        self.assertEqual(test_query[0].field_d1_int, 2)


class TestTimeSeriesPerformance(TestCase):
    @unittest.skipUnless(
        "--tag=slow" in sys.argv, "Extremely slow tests only run on demand"
    )
    @tag("slow")
    def test_large_datasets_with_filter__performance(self):
        year_range = range(2010, 2021)
        hubs = me_factories.HubCFactory.create_batch(1000)
        value_date_lists = {
            year: ValueDateListFactory(value_date=montrek_time(year, 1, 1))
            for year in year_range
        }
        null_value_date_list = ValueDateListFactory(value_date=None)
        for hub in hubs:
            me_factories.SatC1Factory.create(
                hub_value_date=me_factories.CHubValueDateFactory(
                    hub=hub, value_date_list=null_value_date_list
                )
            )
            for year in year_range:
                hvd = me_factories.CHubValueDateFactory.create(
                    hub=hub, value_date_list=value_date_lists[year]
                )
                me_factories.SatTSC2Factory(
                    hub_value_date=hvd,
                )
                me_factories.SatTSC3Factory(
                    hub_value_date=hvd,
                )
        repository = HubCRepository()
        filter_data = {
            "request_path": "test_path",
            "filter": {
                "test_path": {
                    "value_date__year": {
                        "filter_value": year_range[0],
                        "filter_negate": False,
                    }
                }
            },
        }
        repository = HubCRepository(session_data=filter_data)
        t1 = datetime.datetime.now()
        repository.receive()
        t2 = datetime.datetime.now()
        self.assertLess(t2 - t1, datetime.timedelta(seconds=1))


class TestTimeSeriesQuerySetEmpty(TestCase):
    def test_empty_queryset(self):
        repo = HubCRepository()
        test_query = repo.receive().filter(field_tsc3_int=42)
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

        test_querysets_dict = repository.get_history_queryset(
            huba.hub_value_date.first().id
        )

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

    def test_reversed_link(self):
        repo = HubBRepository2({"user_id": self.user.id})
        sat_a = me_factories.SatA1Factory()
        repo.create_by_dict(
            {"link_hub_b_hub_a": sat_a.hub_entity, "field_b1_str": "testb1"}
        )
        b1_objs = me_models.SatB1.objects.all()
        self.assertEqual(b1_objs.count(), 1)

        repo = HubBRepository2({"user_id": self.user.id})
        sat_a = me_factories.SatA1Factory()
        repo.create_by_dict(
            {
                "link_hub_b_hub_a": sat_a.hub_entity,
                "hub_entity_id": b1_objs.first().hub_entity.id,
            }
        )
        b1_objs = me_models.SatB1.objects.all()
        self.assertEqual(b1_objs.count(), 1)
        repo = HubBRepository2({"user_id": self.user.id})
        b1_obj = repo.receive().get()
        test_queryset = repo.get_history_queryset(b1_obj.pk)
        history_links = test_queryset["LinkHubAHubB"]
        self.assertEqual(history_links.count(), 2)
        self.assertEqual(
            history_links.first().state_date_start,
            history_links.last().state_date_end,
        )


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
        repository_b.store_in_view_model()
        satb_queryset = repository_b.receive()
        self.assertEqual(satb_queryset.count(), 2)
        satb_queryset = satb_queryset.order_by("field_b1_str")
        self.assertEqual(
            satb_queryset[0].hub_d_id,
            f"{self.satd1.hub_entity_id},{self.satd2.hub_entity_id}",
        )
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
        satd_queryset = repository_d.receive()
        self.assertEqual(satd_queryset.count(), 2)
        self.assertEqual(
            satd_queryset[0].hub_b_id,
            f"{self.satb1.hub_entity_id},{self.satb2.hub_entity_id}",
        )
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
        new_sat_b = repository_b.receive().last()
        links = new_sat_b.hub.link_hub_b_hub_d.all()
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

        hub_b = repository_b.receive().filter(hub__id=hub_entity_id).first()

        links = me_models.LinkHubBHubD.objects.filter(hub_in=hub_b.hub.id).all()
        continued = links.filter(hub_out=self.satd1.hub_entity).get()
        discontinued = links.filter(hub_out=self.satd2.hub_entity).get()
        new_1 = links.filter(hub_out=satd3.hub_entity).get()
        new_2 = links.filter(hub_out=satd4.hub_entity).get()

        self.assertEqual(hub_b.field_d1_str, "erster,dritter,vierter")

        self.assertEqual(continued.state_date_start, MIN_DATE)
        self.assertEqual(continued.state_date_end, MAX_DATE)
        self.assertEqual(discontinued.state_date_start, MIN_DATE)
        self.assertLess(discontinued.state_date_end, MAX_DATE)
        self.assertEqual(new_1.state_date_start, new_2.state_date_start)
        self.assertEqual(new_1.state_date_end, MAX_DATE)
        self.assertEqual(new_2.state_date_end, MAX_DATE)

    def test_json_field__from_dict(self):
        test_dict = {"key": "value"}
        test_hub = me_models.HubA.objects.create()
        HubAJsonRepository(session_data={"user_id": self.user.id}).std_create_object(
            {
                "hub_entity_id": test_hub.id,
                "field_a3_json": test_dict,
                "field_a3_str": "test",
            }
        )
        test_object = me_models.SatA3.objects.get(hub_entity=test_hub)
        self.assertEqual(test_object.field_a3_json, test_dict)

    def test_json_field__from_str(self):
        test_str = '{"key": "value"}'
        test_hub = me_models.HubA.objects.create()
        HubAJsonRepository(session_data={"user_id": self.user.id}).std_create_object(
            {
                "hub_entity_id": test_hub.id,
                "field_a3_json": test_str,
                "field_a3_str": "test",
            }
        )
        test_object = me_models.SatA3.objects.get(hub_entity=test_hub)
        self.assertEqual(test_object.field_a3_json, {"key": "value"})

    def test_json_field__from_dataframe(self):
        test_str = '{"key": "value"}'
        test_hub = me_models.HubA.objects.create()
        HubAJsonRepository(
            session_data={"user_id": self.user.id}
        ).create_objects_from_data_frame(
            pd.DataFrame(
                {
                    "hub_entity_id": [test_hub.id],
                    "field_a3_json": [test_str],
                    "field_a3_str": ["test1"],
                }
            )
        )
        test_objects = me_models.SatA3.objects.all()
        for to in test_objects:
            self.assertEqual(to.field_a3_json, {"key": "value"})

    def test_json_field__from_str_single_quote(self):
        test_str = "{'key': 'value'}"
        test_hub = me_models.HubA.objects.create()
        HubAJsonRepository(session_data={"user_id": self.user.id}).std_create_object(
            {
                "hub_entity_id": test_hub.id,
                "field_a3_json": test_str,
                "field_a3_str": "test",
            }
        )
        test_object = me_models.SatA3.objects.get(hub_entity=test_hub)
        self.assertEqual(test_object.field_a3_json, {"key": "value"})


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


class TestGetHubsByFieldValues(TestCase):
    def setUp(self):
        a1_str_values = ["a", "b", "c", "c", "", "x", "y", "z"]
        for hub_id, a1_str_value in enumerate(a1_str_values):
            hub = me_factories.HubAFactory(id=hub_id + 1)
            me_factories.SatA1Factory(
                hub_entity=hub,
                state_date_start=montrek_time(2023, 7, 10),
                field_a1_str=a1_str_value,
            )

    def test_get_hubs_by_field_values(self):
        values = ["a", "b", "b", "c", "d", "e"]
        repository = HubARepository()
        repository.store_in_view_model()
        actual = repository.get_hubs_by_field_values(
            values=values,
            by_repository_field="field_a1_str",
            raise_for_multiple_hubs=False,
            raise_for_unmapped_values=False,
        )
        actual_ids = [hub.id if hub else None for hub in actual]
        expected_ids = [1, 2, 2, 3, None, None]  # 2 is the first hub with value "c"
        self.assertEqual(actual_ids, expected_ids)

    def test_get_hubs_by_field_values_raises_error_for_multiple_hubs(self):
        values = ["a", "b", "c", "d", "e"]
        repository = HubARepository()
        repository.store_in_view_model()
        with self.assertRaisesMessage(
            MontrekError,
            "Multiple HubA objects found for field_a1_str values (truncated): c",
        ):
            repository.get_hubs_by_field_values(
                values=values,
                by_repository_field="field_a1_str",
                raise_for_multiple_hubs=True,
                raise_for_unmapped_values=False,
            )

    def test_get_hubs_by_field_values_raises_error_for_unmapped_values(self):
        values = ["a", "b", "c", "d", "e"]
        repository = HubARepository()
        repository.store_in_view_model()
        with self.assertRaisesMessage(
            MontrekError,
            "Cannot find HubA objects for field_a1_str values (truncated): d, e",
        ):
            repository.get_hubs_by_field_values(
                values=values,
                by_repository_field="field_a1_str",
                raise_for_multiple_hubs=False,
                raise_for_unmapped_values=True,
            )

    def test_get_hubs_by_field_values__timeseries(self):
        sat = me_factories.SatTSC2Factory(field_tsc2_float=3.0)
        repository = HubCRepository()
        test_hubs = repository.get_hubs_by_field_values(
            values=[3.0],
            by_repository_field="field_tsc2_float",
            raise_for_multiple_hubs=False,
            raise_for_unmapped_values=False,
        )
        self.assertEqual(test_hubs[0], sat.hub_value_date.hub)


class TestRepositoryQueryConcept(TestCase):
    def test_satellite_concept__single_static_entry(self):
        c1_fac = me_factories.SatC1Factory(
            field_c1_str="Hallo",
            field_c1_bool=True,
        )
        repo = HubCRepository({})
        query = repo.receive()
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().field_c1_str, c1_fac.field_c1_str)
        self.assertEqual(query.first().field_c1_bool, c1_fac.field_c1_bool)
        self.assertEqual(query.first().hub_entity_id, c1_fac.hub_entity_id)
        self.assertEqual(query.first().value_date, None)

    def test_ts_satellite_concept__single_entry(self):
        tsc2_fac = me_factories.SatTSC2Factory.create()
        repo = HubCRepository({})
        query = repo.receive()
        self.assertEqual(query.first().field_tsc2_float, tsc2_fac.field_tsc2_float)
        self.assertEqual(
            query.first().value_date,
            tsc2_fac.hub_value_date.value_date_list.value_date,
        )

    def test_ts_satellite_concept__two_hubs(self):
        tsc2_fac1 = me_factories.SatTSC2Factory.create(
            field_tsc2_float=10, value_date="2024-11-13"
        )
        tsc2_fac2 = me_factories.SatTSC2Factory.create(
            field_tsc2_float=20, value_date="2024-11-14"
        )
        repo = HubCRepository({})
        query = repo.receive()
        self.assertEqual(query.count(), 2)
        query_1 = query.get(value_date="2024-11-13")
        query_2 = query.get(value_date="2024-11-14")
        self.assertEqual(query_1.field_tsc2_float, tsc2_fac1.field_tsc2_float)
        self.assertEqual(query_2.field_tsc2_float, tsc2_fac2.field_tsc2_float)

    def test_ts_satellite_concept__two_dates(self):
        tsc2_fac1 = me_factories.SatTSC2Factory.create(
            field_tsc2_float=10, value_date="2024-11-14"
        )
        tsc2_fac2 = me_factories.SatTSC2Factory.create(
            field_tsc2_float=20,
            hub_value_date__hub=tsc2_fac1.hub_value_date.hub,
            value_date="2024-11-13",
        )
        repo = HubCRepository({})
        query = repo.receive()
        self.assertEqual(query.count(), 2)
        self.assertEqual(query.first().field_tsc2_float, tsc2_fac1.field_tsc2_float)
        self.assertEqual(query.last().field_tsc2_float, tsc2_fac2.field_tsc2_float)
        self.assertEqual(
            str(query.first().value_date),
            tsc2_fac1.hub_value_date.value_date_list.value_date,
        )
        self.assertEqual(
            str(query.last().value_date),
            tsc2_fac2.hub_value_date.value_date_list.value_date,
        )

    def test_ts_satellite_concept__with_sat(self):
        tsc2_fac1 = me_factories.SatTSC2Factory(field_tsc2_float=10)
        c_sat = me_factories.SatC1Factory(
            hub_entity=tsc2_fac1.hub_value_date.hub, field_c1_str="hallo"
        )
        repo = HubCRepository({})
        query = repo.receive()
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().field_tsc2_float, tsc2_fac1.field_tsc2_float)
        self.assertEqual(
            query.first().value_date,
            tsc2_fac1.hub_value_date.value_date_list.value_date,
        )
        self.assertEqual(query.first().field_c1_str, c_sat.field_c1_str)

    def test_ts_satellite_concept__two_ts_sats(self):
        tsc2_fac = me_factories.SatTSC2Factory(field_tsc2_float=10)
        c_sat1 = me_factories.SatC1Factory(
            hub_entity=tsc2_fac.hub_value_date.hub, field_c1_str="hallo"
        )
        tsc3_fac = me_factories.SatTSC3Factory(
            field_tsc3_int=20, hub_value_date=tsc2_fac.hub_value_date
        )
        repo = HubCRepository({})
        query = repo.receive()
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().field_tsc2_float, tsc2_fac.field_tsc2_float)
        self.assertEqual(
            query.first().value_date,
            tsc2_fac.hub_value_date.value_date_list.value_date,
        )
        self.assertEqual(query.first().field_c1_str, c_sat1.field_c1_str)
        self.assertEqual(query.first().field_tsc3_int, tsc3_fac.field_tsc3_int)

    def test_ts_satellite_concept__linked_sat(self):
        c_hub_value_date = me_factories.CHubValueDateFactory.create()
        c_sat1 = me_factories.SatC1Factory(
            field_c1_str="hallo", hub_entity=c_hub_value_date.hub
        )
        d_sat1 = me_factories.SatD1Factory.create(
            field_d1_str="test",
        )
        c_sat1.hub_entity.link_hub_c_hub_d.add(d_sat1.hub_entity)
        repo = HubCRepository({})
        query = repo.receive()
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().field_c1_str, c_sat1.field_c1_str)
        self.assertEqual(query.first().field_d1_str, d_sat1.field_d1_str)

    def test_ts_satellite_concept__linked_ts_sat(self):
        value_date_list = me_factories.ValueDateListFactory()
        c_hub_value_date = me_factories.CHubValueDateFactory.create(
            value_date_list=value_date_list
        )
        d_hub_value_date = me_factories.DHubValueDateFactory.create(
            value_date_list=value_date_list
        )
        d_hub_value_date2 = me_factories.DHubValueDateFactory.create(
            hub=d_hub_value_date.hub
        )
        c_sat = me_factories.SatTSC2Factory.create(
            hub_value_date=c_hub_value_date, field_tsc2_float=10
        )
        d_sat = me_factories.SatTSD2Factory.create(
            hub_value_date=d_hub_value_date, field_tsd2_float=20
        )
        me_factories.SatTSD2Factory.create(
            field_tsd2_float=30, hub_value_date=d_hub_value_date2
        )
        c_hub_value_date.hub.link_hub_c_hub_d.add(d_hub_value_date.hub)
        repo = HubCRepository({})
        query = repo.receive()
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().field_tsc2_float, c_sat.field_tsc2_float)
        self.assertEqual(query.first().field_tsd2_float, str(d_sat.field_tsd2_float))

    def test_ts_satellite_concept__two_ts_sats_different_dates(self):
        tsc2_fac1 = me_factories.SatTSC2Factory(
            field_tsc2_float=10, value_date="2024-11-13"
        )
        c_sat1 = me_factories.SatC1Factory(
            hub_entity=tsc2_fac1.hub_value_date.hub, field_c1_str="hallo"
        )
        tsc3_fac = me_factories.SatTSC3Factory(
            field_tsc3_int=20, hub_value_date=tsc2_fac1.hub_value_date
        )
        tsc3_fac_2 = me_factories.SatTSC3Factory(
            field_tsc3_int=30, value_date="2024-11-15"
        )
        c_sat2 = me_factories.SatC1Factory(
            hub_entity=tsc3_fac_2.hub_value_date.hub, field_c1_str="wallo"
        )
        repo = HubCRepository({})
        query = repo.receive()
        self.assertEqual(query.count(), 2)
        result_1 = query.get(value_date="2024-11-13")
        result_2 = query.get(value_date="2024-11-15")
        self.assertEqual(result_1.field_tsc2_float, tsc2_fac1.field_tsc2_float)
        self.assertEqual(
            result_1.value_date,
            tsc2_fac1.hub_value_date.value_date_list.value_date,
        )
        self.assertEqual(result_1.field_c1_str, c_sat1.field_c1_str)
        self.assertEqual(result_1.field_tsc3_int, tsc3_fac.field_tsc3_int)
        self.assertEqual(result_2.field_tsc2_float, None)
        self.assertEqual(
            str(result_2.value_date),
            tsc3_fac_2.hub_value_date.value_date_list.value_date,
        )
        self.assertEqual(result_2.field_c1_str, c_sat2.field_c1_str)
        self.assertEqual(result_2.field_tsc3_int, tsc3_fac_2.field_tsc3_int)

    def test_ts_satellite_concept__many_to_many_link(self):
        c_sat1 = me_factories.SatC1Factory(field_c1_str="hallo")
        c_sat2 = me_factories.SatC1Factory(field_c1_str="hallo2")
        d_sat1 = me_factories.SatD1Factory.create(
            field_d1_str="test",
        )
        d_sat2 = me_factories.SatD1Factory.create(
            field_d1_str="test2",
        )
        c_sat1.hub_entity.link_hub_c_hub_d.add(d_sat1.hub_entity)
        c_sat1.hub_entity.link_hub_c_hub_d.add(d_sat2.hub_entity)
        c_sat2.hub_entity.link_hub_c_hub_d.add(d_sat1.hub_entity)
        repo = HubCRepository({})
        query = repo.receive()
        self.assertEqual(query.count(), 2)
        self.assertEqual(query.first().field_c1_str, c_sat1.field_c1_str)
        self.assertEqual(
            query.first().field_d1_str, f"{d_sat1.field_d1_str},{d_sat2.field_d1_str}"
        )
        self.assertEqual(query.last().field_c1_str, c_sat2.field_c1_str)
        self.assertEqual(query.last().field_d1_str, d_sat1.field_d1_str)

    def test_ts_satellite_concept__multiple_ts_links_aggregated_to_one(self):
        c_sat1 = me_factories.SatC1Factory()
        tsd2_fac1 = me_factories.SatTSD2Factory(
            field_tsd2_float=10, value_date="2019-09-09"
        )
        tsd2_fac2 = me_factories.SatTSD2Factory(
            field_tsd2_float=20,
            hub_entity=tsd2_fac1.hub_value_date.hub,
            value_date="2024-09-09",
        )
        c_sat1.hub_entity.link_hub_c_hub_d.add(tsd2_fac1.hub_value_date.hub)
        tsd2_fac3 = me_factories.SatTSD2Factory(
            field_tsd2_float=30, value_date="2019-09-09"
        )
        tsd2_fac3 = me_factories.SatTSD2Factory(
            field_tsd2_float=40,
            hub_entity=tsd2_fac3.hub_value_date.hub,
            value_date="2024-09-09",
        )
        c_sat1.hub_entity.link_hub_c_hub_d.add(tsd2_fac3.hub_value_date.hub)
        repo = HubCRepository({})
        query = repo.receive()
        self.assertEqual(query.first().field_tsd2_float_agg, 100.0)
        self.assertEqual(query.first().field_tsd2_float_latest, 60.0)


class TestCommonFields(TestCase):
    def test_commom_comments(self):
        tsc2 = me_factories.SatTSC2Factory.create(
            comment="First Comment", value_date="2019-09-09"
        )
        tsd2 = me_factories.SatTSD2Factory.create(
            comment="Third Comment", value_date="2019-09-09"
        )
        c1 = me_factories.SatC1Factory.create(
            comment="Second Comment", hub_entity=tsc2.hub_value_date.hub
        )
        d1 = me_factories.SatD1Factory.create(
            comment="Fourth Comment", hub_entity=tsd2.hub_value_date.hub
        )
        c1.hub_entity.link_hub_c_hub_d.add(d1.hub_entity)

        query = HubCRepositoryCommonFields().receive()
        test_obj = query.last()
        self.assertEqual(test_obj.comment_tsc2, "First Comment")
        self.assertEqual(test_obj.comment_c1, "Second Comment")
        self.assertEqual(test_obj.comment_tsd2, "Third Comment")
        self.assertEqual(test_obj.comment_d1, "Fourth Comment")
        self.assertEqual(test_obj.comment, "")


class TestReceiveWithFilter(TestCase):
    def test_receive_with_filter(self):
        me_factories.SatC1Factory.create(field_c1_str="Test")
        me_factories.SatC1Factory.create(field_c1_str="Test2")
        me_factories.SatC1Factory.create(field_c1_str="Test3")
        filter_data = {
            "request_path": "test_path",
            "filter": {
                "test_path": {
                    "field_c1_str": {
                        "filter_value": "Test",
                        "filter_negate": False,
                    }
                }
            },
        }
        repo = HubCRepository(session_data=filter_data)
        query = repo.receive()
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().field_c1_str, "Test")

    def test_receive_with_filter_dont_apply(self):
        me_factories.SatC1Factory.create(field_c1_str="Test")
        me_factories.SatC1Factory.create(field_c1_str="Test2")
        me_factories.SatC1Factory.create(field_c1_str="Test3")
        filter_data = {
            "request_path": "test_path",
            "filter": {
                "test_path": {
                    "field_c1_str": {
                        "filter_value": "Test",
                        "filter_negate": False,
                    }
                }
            },
        }
        repo = HubCRepository(session_data=filter_data)
        query = repo.receive(apply_filter=False)
        self.assertEqual(query.count(), 3)

    def test_ignore_session_date(self):
        hub_value_date = me_factories.CHubValueDateFactory.create(
            value_date="2024-02-05"
        )
        me_factories.SatC1Factory.create(
            field_c1_str="Test", hub_entity=hub_value_date.hub
        )
        repo = HubCRepositoryOnlyStatic(
            session_data={"end_date": datetime.datetime(2024, 1, 1)}
        )
        test_query = repo.receive()
        self.assertEqual(test_query.count(), 1)
        self.assertEqual(test_query.first().field_c1_str, "Test")


class TestObjectToDict(TestCase):
    def test_object_to_dict_with_link(self):
        a_sat = me_factories.SatA1Factory.create(field_a1_str="TestA", field_a1_int=1)
        b_sat = me_factories.SatB1Factory.create(
            field_b1_str="TestB", field_b1_date="2024-02-05"
        )
        a_sat.hub_entity.link_hub_a_hub_b.add(b_sat.hub_entity)

        repo = HubARepository()
        repo.store_in_view_model()
        query = repo.receive().first()
        test_dict = repo.object_to_dict(query)
        self.assertEqual(test_dict["field_a1_str"], "TestA")
        self.assertEqual(test_dict["field_a1_int"], 1)
        self.assertEqual(test_dict["field_b1_str"], "TestB")
        self.assertEqual(test_dict["field_b1_date"], montrek_time(2024, 2, 5).date())


class TestSecurity(TestCase):
    def test_avoid_write_hacked_strings(self):
        user = MontrekUserFactory()
        repo = HubARepository({"user_id": user.id})
        repo.create_by_dict({"field_a1_str": "<b><script>HACKED!!</script></b>"})
        obj = repo.receive().first()
        self.assertEqual(obj.field_a1_str, "<b>HACKED!!</b>")


class TestRepositoryViewModel(TestCase):
    def setUp(self) -> None:
        user = MontrekUserFactory()
        self.repo = HubARepository({"user_id": user.id})

    def tearDown(self) -> None:
        del self.repo

    def test_create_view_model(self):
        repo_view = self.repo.view_model
        self.assertTrue(issubclass(repo_view, models.Model))
        test_instance = repo_view(field_a1_str="Test")
        self.assertEqual(test_instance.field_a1_str, "Test")
        for field in self.repo.annotator.get_annotated_field_names():
            if field in ["hub_entity_id"]:
                continue
            self.assertTrue(hasattr(test_instance, field))

    def test_model_view_created_on_class_level(self):
        side_repo = HubARepository()
        self.assertTrue(issubclass(side_repo.view_model, models.Model))

    def test_view_model_exists_after_create(self):
        self.repo.create_by_dict({"field_a1_str": "Field"})
        repo_view = self.repo.view_model
        self.assertTrue(issubclass(repo_view, models.Model))

    def test_view_model_writes_to_db(self):
        hub_a = me_factories.HubAFactory()
        repo_view = self.repo.view_model
        instance = repo_view(
            field_a1_str="Test",
            value_date="2025-01-02",
            created_at="2025-01-02",
            created_by="test@tester.de",
            hub=hub_a,
        )
        instance.save()
        received_instance = repo_view.objects.first()
        self.assertEqual(received_instance.field_a1_str, "Test")

    def test_view_model_is_filled_after_create(self):
        self.repo.create_by_dict({"field_a1_str": "Field"})
        repo_view = self.repo.view_model
        instance = repo_view.objects.first()
        self.assertEqual(instance.field_a1_str, "Field")

    def test_view_model_received_by_repo(self):
        hub_a = me_factories.HubAFactory()
        repo_view = self.repo.view_model
        instance = repo_view(
            field_a1_str="Test",
            value_date="2025-01-02",
            created_at="2025-01-02",
            created_by="test@tester.de",
            hub=hub_a,
        )
        instance.save()
        received_instance = self.repo.receive().first()
        self.assertEqual(received_instance.field_a1_str, "Test")

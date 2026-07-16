import datetime
import json
from unittest.mock import patch

import numpy as np
import pandas as pd
from baseclasses.errors.montrek_user_error import MontrekError
from baseclasses.repositories.montrek_repository import MontrekRepository
from baseclasses.repositories.subquery_builder import (
    CrossSatelliteFilter,
    ReverseLinkedSatelliteSubqueryBuilder,
)
from baseclasses.tests.factories.montrek_factory_schemas import ValueDateListFactory
from baseclasses.utils import montrek_time
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from freezegun import freeze_time
from montrek_example.models import example_models as me_models
from montrek_example.repositories.hub_a_repository import (
    HubAJsonRepository,
    HubAQuerysetAwareRepository,
    HubARepository,
    HubARepository2,
    HubARepository3,
    HubARepository4,
    HubARepository5,
    HubARepository6,
    HubARepository7,
    HubARepositoryLinkSatelliteQFilter,
    HubATSLinkedRepository,
)
from montrek_example.repositories.hub_b_repository import (
    HubBRepository,
    HubBRepository2,
    HubBRepositoryDirectLinkHub,
    HubBRepositoryWithCrossSatFilter,
)
from montrek_example.repositories.hub_c_repository import (
    HubCBooleanRepository,
    HubCRepository,
    HubCRepository2,
    HubCRepositoryAll,
    HubCRepositoryCommonFields,
    HubCRepositoryCount,
    HubCRepositoryDirectLinkHub,
    HubCRepositoryJsonAgg,
    HubCRepositoryLast,
    HubCRepositoryLastTS,
    HubCRepositoryLinkSatelliteQFilter,
    HubCRepositoryLinkSatelliteQOuterRefFilter,
    HubCRepositoryMean,
    HubCRepositoryOnlyStatic,
    HubCRepositoryPropertyFilter,
    HubCRepositoryReversedParents,
    HubCRepositoryReversedParentsNoMatchingReversedParents,
    HubCRepositorySumTS,
    HubCRepositoryViewModel,
    HubCRepositoryWithManyToManyParents,
    HubCRepositoryWithManyToOneParents,
    HubCRepositoryWithPairedJsonAnnotation,
    HubCRepositoryWithValueDateScopedLink,
)
from montrek_example.repositories.hub_d_repository import (
    HubDRepository,
    HubDRepositoryReversedParentLink,
    HubDRepositoryTSReverseLink,
    HubDTSLinkAggRepositorySum,
    HubDTSLinkAggRepositoryWithLinkHubValueDateFilter,
)
from montrek_example.repositories.hub_e_repository import HubERepository
from montrek_example.tests.factories import montrek_example_factories as me_factories
from user.tests.factories.montrek_user_factories import MontrekUserFactory

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

    def test_get_identifier_fields(self):
        repo = HubARepository()
        id_fields = repo.get_identifier_fields()
        self.assertCountEqual(id_fields, ["field_a1_str", "field_a2_str"])

    def test_get_identifier_fields_with_linked_satellites(self):
        repo = HubDRepository()
        id_fields = repo.get_identifier_fields()
        self.assertCountEqual(id_fields, ["field_d1_str", "hub_value_date_id"])

    def test_get_identifier_fields_excludes_linked_satellite_ids(self):
        repo = HubBRepository()
        id_fields = repo.get_identifier_fields()
        self.assertCountEqual(
            id_fields, ["field_b1_str", "field_b2_str", "hub_entity_id"]
        )
        self.assertNotIn("field_d1_str", id_fields)

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
        # Fields are returned in registration order (set_annotations call order),
        # with renames applied in-place.  HubARepository.set_annotations registers:
        #   SatA1 (field_a1_int, field_a1_str), SatA2 (field_a2_float, field_a2_str),
        #   SatB1 via LinkHubAHubB (field_b1_str, field_b1_date).
        # The test then adds SatTSC2 (field_tsc2_float) and renames two fields.
        self.assertEqual(
            test_fields,
            [
                "value_date",
                "hub_entity_id",
                "created_at",
                "created_by",
                "comment",
                "field_a1_int",
                "my_field_a1_str",
                "field_a2_float",
                "field_a2_str",
                "my_field_b1_str",
                "field_b1_date",
                "field_tsc2_float",
            ],
        )
        # Fields are returned in registration order.  HubCRepository.set_annotations
        # registers direct satellite fields (SatTSC2, SatTSC3, SatTSC4, SatC1) first,
        # then linked satellite fields (SatD1, SatTSD2 via LinkHubCHubD).
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
                "hub_d_id",
                "field_d1_int",
                "field_tsd2_float",
                "field_tsd2_int",
                "field_tsd2_float_agg",
                "field_tsd2_float_latest",
            ],
        )

    def test_build_queryset_with_satellite_fields(self):
        repository = HubARepository({"reference_date": montrek_time(2023, 7, 8)})
        queryset = repository.test_queryset_1()

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_a1_int, 5)
        self.assertEqual(queryset[1].field_a1_int, None)
        self.assertEqual(queryset[0].field_a2_float, 8.0)
        self.assertEqual(queryset[1].field_a2_float, 9.0)

        repository = HubARepository({"reference_date": montrek_time(2023, 7, 10)})
        queryset = repository.test_queryset_1()

        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_a1_int, 6)
        self.assertEqual(queryset[1].field_a1_int, None)
        self.assertEqual(queryset[0].field_a2_float, 8.0)
        self.assertEqual(queryset[1].field_a2_float, None)

        repository = HubARepository({"reference_date": montrek_time(2023, 7, 15)})
        queryset = repository.test_queryset_1()

        self.assertEqual(queryset[0].field_a1_int, 6)
        self.assertEqual(queryset[1].field_a1_int, None)
        self.assertEqual(queryset[0].field_a2_float, 8.0)
        self.assertEqual(queryset[1].field_a2_float, None)

        repository = HubARepository({"reference_date": montrek_time(2023, 7, 20)})
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

    def test_std_create_object_comment_none(self):
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "field_a1_int": 5,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
                "field_a2_str": "test2",
                "comment": None,
            }
        )
        self.assertEqual(me_models.SatA1.objects.first().comment, "")
        self.assertEqual(me_models.SatA2.objects.first().comment, "")

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
        repository.store_in_view_model()
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

    def test_dont_update_satellite_with_hub_entity_id_as_identifier_field(self):
        self.assertEqual(me_models.SatA4.objects.count(), 0)
        sat = me_factories.SatA4Factory.create(field_a4_str="Test")
        self.assertEqual(me_models.SatA4.objects.count(), 1)
        HubARepository4({"user_id": self.user.id}).create_by_dict(
            {"hub_entity_id": sat.hub_entity_id, "field_a4_str": "Test"}
        )
        self.assertEqual(me_models.SatA4.objects.count(), 1)

    def test_std_create__only_booleans(self):
        repo = HubCBooleanRepository({"user_id": self.user.id})
        repo.create_by_dict({"field_bool_1": False, "field_bool_2": False})
        created_satellites = me_models.SatCBoolean.objects.all()
        self.assertEqual(created_satellites.count(), 1)
        created_sat = created_satellites.first()
        self.assertFalse(created_sat.field_bool_1)
        self.assertFalse(created_sat.field_bool_2)

    def test_dont_attempt_to_write_link_when_field_is_unknown(self):
        test_hub = me_factories.HubBFactory()
        repo = HubARepository({"user_id": self.user.id})
        repo.create_by_dict({"field_a1_str": "Hallo", "dummy_field": test_hub})
        self.assertEqual(repo.receive().count(), 1)


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

    def test_create_satellite_with_given_hub__view_model(self):
        hub = me_factories.HubAFactory()
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "hub_entity_id": hub.id,
                "field_a1_str": "test",
                "field_a2_float": 6.0,
            }
        )
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 1)
        queried_object = test_query.get()
        self.assertEqual(queried_object.field_a1_str, "test")
        self.assertEqual(queried_object.field_a2_float, 6.0)
        self.assertEqual(queried_object.hub_entity_id, hub.id)

    def test_create_ts_satellite_with_given_hub__view_model(self):
        hub = me_factories.HubCFactory()
        repository = HubCRepositoryViewModel(session_data={"user_id": self.user.id})
        repository.std_create_object(
            {
                "hub_entity_id": hub.id,
                "value_date": "2025-10-20",
                "field_tsc2_float": 6.0,
            }
        )
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 1)
        queried_object = test_query.get()
        self.assertEqual(queried_object.field_tsc2_float, 6.0)
        self.assertEqual(queried_object.hub_entity_id, hub.id)

    def test_create_satellite_with_given_satellite__view_model(self):
        sat = me_factories.SatA1Factory(field_a1_str="test")
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.store_in_view_model()
        repository.create_by_data_frame(
            pd.DataFrame(
                {
                    "hub_entity_id": [sat.hub_entity.pk],
                    "field_a2_float": [6.0],
                }
            )
        )
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 1)
        queried_object = test_query.get()
        self.assertEqual(queried_object.field_a1_str, "test")
        self.assertEqual(queried_object.field_a2_float, 6.0)
        self.assertEqual(queried_object.hub_entity_id, sat.hub_entity.id)

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

    def test_write_reversed_links_via_data_frame(self):
        repository = HubDRepository(session_data={"user_id": self.user.id})
        sat_b = me_factories.SatB1Factory(field_b1_str="Test B")
        input_data = pd.DataFrame(
            {"field_d1_str": ["Test D"], "link_hub_d_hub_b": [sat_b.hub_entity]}
        )
        repository.create_by_data_frame(input_data)
        test_data = repository.receive()
        self.assertEqual(test_data.count(), 1)
        self.assertEqual(test_data[0].field_d1_str, "Test D")
        self.assertEqual(json.loads(test_data[0].field_b1_str), ["Test B"])


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
        self.assertIsNone(repository.get_db_staller())
        repository.create_objects_from_data_frame(data_frame)
        self.assertIsNotNone(repository.get_db_staller())
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
        received_data = repository.receive()
        self.assertEqual(received_data.count(), 2)

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

    def test_create_objects_from_data_frame__static_data_update(self):
        repository = HubCRepository(session_data={"user_id": self.user.id})
        data_frame = pd.DataFrame(
            {
                "field_c1_str": ["test_static", "test_static2"],
                "field_c1_bool": [True, False],
            }
        )
        repository.create_objects_from_data_frame(data_frame)
        data_frame = pd.DataFrame(
            {
                "field_c1_str": ["test_static", "test_static2"],
                "field_c1_bool": [True, True],
            }
        )
        repository.create_objects_from_data_frame(data_frame)
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 2)
        self.assertEqual(me_models.HubC.objects.count(), 2)
        static_objs = me_models.SatC1.objects
        self.assertEqual(static_objs.count(), 3)
        self.assertTrue(test_query[1].field_c1_bool)
        now = timezone.now()
        old_entry = static_objs.get(field_c1_str="test_static2", state_date_end__lt=now)
        self.assertFalse(old_entry.field_c1_bool)
        old_entry = static_objs.get(field_c1_str="test_static2", state_date_end__gt=now)
        self.assertTrue(old_entry.field_c1_bool)

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

    def test_create_by_data_frame_sat_with_hub_entity_id_identifier(self):
        """
        When a repository has satellites attached which have a field identifier and the hub entity as identifier field,
        the right hub entity has to be found
        """
        hubs = me_factories.HubAFactory.create_batch(2)
        me_factories.SatA1Factory(
            hub_entity=hubs[0], field_a1_str="test_1", field_a1_int=1
        )
        me_factories.SatA1Factory(
            hub_entity=hubs[1], field_a1_str="test_2", field_a1_int=2
        )
        me_factories.SatA4Factory(hub_entity=hubs[0], field_a4_str="A4 1")
        me_factories.SatA4Factory(hub_entity=hubs[1], field_a4_str="A4 2")
        repository = HubARepository6(session_data={"user_id": self.user.id})
        with self.subTest("Upload identical DF does not change DB"):
            upload_df = pd.DataFrame(
                {
                    "field_a1_str": ["test_1", "test_2"],
                    "field_a1_int": [1, 2],
                    "field_a4_str": ["A4 1", "A4 2"],
                }
            )
            sat_a1_objs = me_models.SatA1.objects.all()
            sat_a4_objs = me_models.SatA4.objects.all()
            self.assertEqual(sat_a1_objs.count(), 2)
            self.assertEqual(sat_a4_objs.count(), 2)
            repository.create_by_data_frame(upload_df)
            sat_a1_objs = me_models.SatA1.objects.all()
            sat_a4_objs = me_models.SatA4.objects.all()
            self.assertEqual(sat_a1_objs.count(), 2)
            self.assertEqual(sat_a4_objs.count(), 2)

    def test_std_create_object_update_satellite_id_field_keep_hub(self):
        # Create one object
        repository = HubARepository(session_data={"user_id": self.user.id})
        repository.create_by_data_frame(
            pd.DataFrame(
                {
                    "field_a1_int": [5],
                    "field_a1_str": ["test"],
                    "field_a2_float": [6.0],
                    "field_a2_str": ["test2"],
                }
            )
        )

        a_object = (
            HubARepository(session_data={"user_id": self.user.id}).receive().get()
        )
        repository.create_by_data_frame(
            pd.DataFrame(
                {
                    "field_a1_int": [5],
                    "field_a1_str": ["test_new"],
                    "field_a2_float": [6.0],
                    "field_a2_str": ["test2"],
                    "hub_entity_id": [a_object.hub_entity_id],
                }
            )
        )
        # We should still have one Hub
        self.assertEqual(me_models.HubA.objects.count(), 1)

        # The receive should return the adjusted object
        b_object = HubARepository().receive().get()
        self.assertEqual(b_object.field_a1_str, "test_new")


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

    def test_create_hub_a_with_link_to_hub_b_remove(self):
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
                "link_hub_a_hub_b": None,
            }
        )
        self.assertEqual(me_models.LinkHubAHubB.objects.count(), 1)
        queried_object = repository.receive().get()
        self.assertIsNone(queried_object.field_b1_str)

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

    def test_delete_object_with_links(self):
        sat_d = me_factories.SatD1Factory(field_d1_str="blummsi")
        sat_a = me_factories.SatA1Factory()
        sat_b = me_factories.SatB1Factory(link_d=sat_d, link_a=sat_a)

        pre_delete_query = HubARepository7().receive()
        self.assertEqual(pre_delete_query.first().field_d1_str, "blummsi")
        HubBRepository(session_data={"user_id": self.user.id}).delete(sat_b.hub_entity)
        pre_delete_query = HubARepository7().receive()
        self.assertIsNone(pre_delete_query.first().field_d1_str)

    def test_delete_object_closes_link_where_hub_is_hub_in(self):
        hub_b = me_factories.HubBFactory()
        hub_d = me_factories.HubDFactory()
        hub_b.link_hub_b_hub_d.add(hub_d)

        HubBRepository(session_data={"user_id": self.user.id}).delete(hub_b)

        link = me_models.LinkHubBHubD.objects.get(hub_in=hub_b, hub_out=hub_d)
        self.assertLessEqual(link.state_date_end, timezone.now())

    def test_delete_object_closes_link_where_hub_is_hub_out(self):
        hub_a = me_factories.HubAFactory()
        hub_b = me_factories.HubBFactory()
        hub_a.link_hub_a_hub_b.add(hub_b)

        HubBRepository(session_data={"user_id": self.user.id}).delete(hub_b)

        link = me_models.LinkHubAHubB.objects.get(hub_in=hub_a, hub_out=hub_b)
        self.assertLessEqual(link.state_date_end, timezone.now())

    def test_delete_object_closes_all_links_of_same_class(self):
        hub_b = me_factories.HubBFactory()
        hub_ds = me_factories.HubDFactory.create_batch(3)
        for hub_d in hub_ds:
            hub_b.link_hub_b_hub_d.add(hub_d)

        HubBRepository(session_data={"user_id": self.user.id}).delete(hub_b)

        links = me_models.LinkHubBHubD.objects.filter(hub_in=hub_b)
        self.assertEqual(links.count(), 3)
        for link in links:
            self.assertLessEqual(link.state_date_end, timezone.now())

    def test_delete_object_does_not_close_unrelated_links(self):
        hub_b1 = me_factories.HubBFactory()
        hub_d1 = me_factories.HubDFactory()
        hub_b1.link_hub_b_hub_d.add(hub_d1)
        hub_b2 = me_factories.HubBFactory()
        hub_d2 = me_factories.HubDFactory()
        hub_b2.link_hub_b_hub_d.add(hub_d2)

        HubBRepository(session_data={"user_id": self.user.id}).delete(hub_b1)

        untouched_link = me_models.LinkHubBHubD.objects.get(
            hub_in=hub_b2, hub_out=hub_d2
        )
        self.assertGreater(untouched_link.state_date_end, timezone.now())

    def test_delete_object_does_not_reopen_already_closed_links(self):
        hub_b = me_factories.HubBFactory()
        hub_d = me_factories.HubDFactory()
        hub_b.link_hub_b_hub_d.add(hub_d)
        link = me_models.LinkHubBHubD.objects.get(hub_in=hub_b, hub_out=hub_d)
        already_closed_date = timezone.now() - datetime.timedelta(days=1)
        link.state_date_end = already_closed_date
        link.save()

        HubBRepository(session_data={"user_id": self.user.id}).delete(hub_b)

        link.refresh_from_db()
        self.assertEqual(link.state_date_end, already_closed_date)


class TestreceiveLinkedHubIds(TestCase):
    def test_get_linked_hub_without_sat(self):
        # Consider a scenario, where two hubs are linked, but one has no
        # entry in the satellite
        sat_b = me_factories.SatB1Factory.create(field_b1_str="Test")
        hub_d = me_factories.HubDFactory()
        sat_b.hub_entity.link_hub_b_hub_d.add(hub_d)
        test_data = HubBRepositoryDirectLinkHub({}).receive()
        self.assertEqual(test_data.count(), 1)
        # A hub reached via add_linked_satellites_field_annotations will be empty
        self.assertIsNone(test_data.first().hub_d_id)
        self.assertEqual(test_data.first().hub_d_direct_id, json.dumps([hub_d.pk]))

    def test_get_linked_hub_without_sat__single_entry(self):
        sat_b = me_factories.SatB1Factory.create(field_b1_str="Test")
        hub_a = me_factories.HubAFactory()
        sat_b.hub_entity.link_hub_b_hub_a.add(hub_a)
        test_data = HubBRepositoryDirectLinkHub({}).receive()
        self.assertEqual(test_data.count(), 1)
        self.assertIsNone(test_data.first().hub_a_id)
        self.assertEqual(test_data.first().hub_a_direct_id, hub_a.pk)

    def test_get_linked_hub_without_sat__aggregation(self):
        sat_b = me_factories.SatB1Factory.create(field_b1_str="Test")
        hub_d_1 = me_factories.HubDFactory()
        hub_d_2 = me_factories.HubDFactory()
        sat_b.hub_entity.link_hub_b_hub_d.add(hub_d_1)
        sat_b.hub_entity.link_hub_b_hub_d.add(hub_d_2)
        test_data = HubBRepositoryDirectLinkHub({}).receive()
        self.assertEqual(test_data.count(), 1)
        self.assertIsNone(test_data.first().hub_d_id)
        direct_ids = json.loads(test_data.first().hub_d_direct_id)
        self.assertCountEqual(direct_ids, [hub_d_1.pk, hub_d_2.pk])

    def test_get_linked_hub_without_sat__parent_links(self):
        sat_b = me_factories.SatB1Factory.create(field_b1_str="Test")
        hub_d = me_factories.HubDFactory()
        sat_b.hub_entity.link_hub_b_hub_d.add(hub_d)
        hub_cs = me_factories.HubCFactory.create_batch(3)
        for hub_c in hub_cs:
            hub_d.link_hub_d_hub_c.add(hub_c)
        test_data = HubBRepositoryDirectLinkHub({}).receive()
        self.assertEqual(test_data.count(), 1)
        self.assertIsNone(test_data.first().hub_c_id)
        direct_ids = json.loads(test_data.first().hub_c_direct_id)
        self.assertCountEqual(direct_ids, [hub_c.pk for hub_c in hub_cs])

    def test_no_link__returns_null(self):
        me_factories.SatB1Factory.create(field_b1_str="Test")
        test_data = HubBRepositoryDirectLinkHub({}).receive()
        self.assertEqual(test_data.count(), 1)
        self.assertIsNone(test_data.first().hub_d_direct_id)
        self.assertIsNone(test_data.first().hub_a_direct_id)
        self.assertIsNone(test_data.first().hub_c_direct_id)

    def test_expired_link__is_excluded(self):
        sat_b = me_factories.SatB1Factory.create(field_b1_str="Test")
        hub_d = me_factories.HubDFactory()
        me_factories.LinkHubBHubDFactory(
            hub_in=sat_b.hub_entity,
            hub_out=hub_d,
            state_date_end=montrek_time(2020, 1, 1),
        )
        test_data = HubBRepositoryDirectLinkHub({}).receive()
        self.assertEqual(test_data.count(), 1)
        self.assertIsNone(test_data.first().hub_d_direct_id)

    def test_multiple_hub_bs__results_are_isolated(self):
        sat_b1 = me_factories.SatB1Factory.create(field_b1_str="B1")
        sat_b2 = me_factories.SatB1Factory.create(field_b1_str="B2")
        hub_d1 = me_factories.HubDFactory()
        hub_d2 = me_factories.HubDFactory()
        sat_b1.hub_entity.link_hub_b_hub_d.add(hub_d1)
        sat_b2.hub_entity.link_hub_b_hub_d.add(hub_d2)
        test_data = HubBRepositoryDirectLinkHub({}).receive()
        self.assertEqual(test_data.count(), 2)
        b1_row = test_data.get(field_b1_str="B1")
        b2_row = test_data.get(field_b1_str="B2")
        self.assertEqual(b1_row.hub_d_direct_id, json.dumps([hub_d1.pk]))
        self.assertEqual(b2_row.hub_d_direct_id, json.dumps([hub_d2.pk]))

    def test_parent_link__multiple_hub_ds_aggregated(self):
        # HubB → HubD1 → HubC1, HubB → HubD2 → HubC2: both HubC IDs aggregated
        sat_b = me_factories.SatB1Factory.create(field_b1_str="Test")
        hub_d1 = me_factories.HubDFactory()
        hub_d2 = me_factories.HubDFactory()
        sat_b.hub_entity.link_hub_b_hub_d.add(hub_d1)
        sat_b.hub_entity.link_hub_b_hub_d.add(hub_d2)
        hub_c1 = me_factories.HubCFactory()
        hub_c2 = me_factories.HubCFactory()
        hub_d1.link_hub_d_hub_c.add(hub_c1)
        hub_d2.link_hub_d_hub_c.add(hub_c2)
        test_data = HubBRepositoryDirectLinkHub({}).receive()
        self.assertEqual(test_data.count(), 1)
        direct_ids = json.loads(test_data.first().hub_c_direct_id)
        self.assertCountEqual(direct_ids, [hub_c1.pk, hub_c2.pk])

    def test_parent_link__expired_parent_link__returns_null(self):
        # Expired B→D link means HubC reached via that HubD must not appear
        sat_b = me_factories.SatB1Factory.create(field_b1_str="Test")
        hub_d = me_factories.HubDFactory()
        me_factories.LinkHubBHubDFactory(
            hub_in=sat_b.hub_entity,
            hub_out=hub_d,
            state_date_end=montrek_time(2020, 1, 1),
        )
        hub_c = me_factories.HubCFactory()
        hub_d.link_hub_d_hub_c.add(hub_c)
        test_data = HubBRepositoryDirectLinkHub({}).receive()
        self.assertEqual(test_data.count(), 1)
        self.assertIsNone(test_data.first().hub_c_direct_id)

    def test_parent_link__unrelated_hub_d_does_not_bleed(self):
        # HubD → HubC exists, but this HubB has no link to that HubD
        me_factories.SatB1Factory.create(field_b1_str="Test")
        hub_d = me_factories.HubDFactory()
        hub_c = me_factories.HubCFactory()
        hub_d.link_hub_d_hub_c.add(hub_c)
        test_data = HubBRepositoryDirectLinkHub({}).receive()
        self.assertEqual(test_data.count(), 1)
        self.assertIsNone(test_data.first().hub_c_direct_id)

    def test_reversed_link__one_to_many(self):
        sat_c = me_factories.SatC1Factory.create(field_c1_str="Test")
        hub_as = me_factories.HubAFactory.create_batch(3)
        for hub_a in hub_as:
            hub_a.link_hub_a_hub_c.add(sat_c.hub_entity)

        test_data = HubCRepositoryDirectLinkHub({}).receive()
        self.assertIsNone(test_data.first().hub_a_id)
        direct_ids = json.loads(test_data.first().hub_a_direct_id)
        self.assertCountEqual(direct_ids, [hub_a.pk for hub_a in hub_as])


class TestMontrekRepositoryLinks(TestCase):
    def setUp(self):
        self.huba1 = me_factories.HubAFactory()
        self.huba2 = me_factories.HubAFactory()
        me_factories.AHubValueDateFactory(hub=self.huba2, value_date=None)
        self.hubc1 = me_factories.HubCFactory()
        hubc2 = me_factories.HubCFactory()

        me_factories.SatA1Factory(
            hub_entity=self.huba1,
            field_a1_int=5,
            field_a1_str="Test",
        )
        me_factories.LinkHubAHubCFactory(
            hub_in=self.huba1,
            hub_out=self.hubc1,
        )
        me_factories.LinkHubAHubCFactory(
            hub_in=self.huba2,
            hub_out=self.hubc1,
            state_date_end=montrek_time(2023, 7, 12),
        )
        me_factories.LinkHubAHubCFactory(
            hub_in=self.huba2,
            hub_out=hubc2,
            state_date_start=montrek_time(2023, 7, 12),
        )
        me_factories.SatC1Factory(
            hub_entity=self.hubc1,
            state_date_end=montrek_time(2023, 7, 10),
            field_c1_str="First",
        )
        me_factories.SatC1Factory(
            hub_entity=self.hubc1,
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
        self.assertEqual(json.loads(queryset[0].field_a1_int), [5])
        self.assertEqual(queryset[1].field_a1_int, None)
        repository.reference_date = montrek_time(2023, 7, 15)
        queryset = repository.receive()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(json.loads(queryset[0].field_a1_int), [5])
        self.assertEqual(queryset[1].field_a1_int, None)

    def test_link_reversed__session_data(self):
        repository = HubCRepository2({"reference_date": "2023-07-08"})
        queryset = repository.receive()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(json.loads(queryset[0].field_a1_int), [5])
        self.assertEqual(queryset[1].field_a1_int, None)
        repository = HubCRepository2({"reference_date": ["2023-07-15"]})
        queryset = repository.receive()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(json.loads(queryset[0].field_a1_int), [5])
        self.assertEqual(queryset[1].field_a1_int, None)

    def test_link_reversed_ts(self):
        sat_tsc2 = me_factories.SatTSC2Factory(
            field_tsc2_float=2.5, value_date="2024-11-19"
        )
        d_hub = me_factories.DHubValueDateFactory(value_date="2024-11-19").hub
        sat_tsc2.hub_value_date.hub.link_hub_c_hub_d.add(d_hub)
        queryset = HubDRepositoryTSReverseLink({}).receive()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(json.loads(queryset[0].field_tsc2_float), [2.5])

    def test_link_with_parent_links(self):
        hubc = me_factories.HubCFactory()
        hubd = me_factories.HubDFactory()
        me_factories.SatD1Factory.create(hub_entity=hubd, field_d1_str="Test")
        me_factories.LinkHubCHubDFactory(hub_in=hubc, hub_out=hubd)
        me_factories.LinkHubAHubCFactory(hub_in=self.huba1, hub_out=hubc)
        repository = HubARepository3()
        queryset = repository.receive()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(
            json.loads(queryset.get(field_d1_str__isnull=False).field_d1_str), ["Test"]
        )

    def test_link_with_parent_links__reference_date_filter_on_parent_link_class(self):
        # Initial setup
        hubc = me_factories.HubCFactory()
        hubd = me_factories.HubDFactory()
        me_factories.SatD1Factory.create(hub_entity=hubd, field_d1_str="Test")
        me_factories.LinkHubCHubDFactory(hub_in=hubc, hub_out=hubd)
        me_factories.LinkHubAHubCFactory(hub_in=self.huba1, hub_out=hubc)
        # Change link from A to C
        hubc2 = me_factories.HubCFactory()
        hubd2 = me_factories.HubDFactory()
        me_factories.SatD1Factory.create(hub_entity=hubd2, field_d1_str="Test2")
        me_factories.LinkHubCHubDFactory(hub_in=hubc2, hub_out=hubd2)
        user = MontrekUserFactory()
        session_data = {"user_id": user.id}
        repository = HubARepository3(session_data)
        new_hub = repository.create_by_dict(
            {"field_a1_str": "Test", "link_hub_a_hub_c": hubc2}
        )
        queryset = repository.receive()
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(
            json.loads(queryset.get(hub_entity_id=new_hub.pk).field_d1_str), ["Test2"]
        )

    def test_link_reversed_with_parent_links(self):
        satd = me_factories.SatD1Factory()
        me_factories.LinkHubCHubDFactory(hub_in=self.hubc1, hub_out=satd.hub_entity)
        sata3 = me_factories.SatA1Factory(field_a1_str="Extra Test")
        hubc2 = me_factories.HubCFactory()
        me_factories.LinkHubAHubCFactory(
            hub_in=sata3.hub_entity,
            hub_out=hubc2,
        )
        me_factories.LinkHubCHubDFactory(hub_in=hubc2, hub_out=satd.hub_entity)
        repository = HubDRepositoryReversedParentLink()
        queryset = repository.receive()
        self.assertEqual(queryset.count(), 1)
        self.assertCountEqual(
            json.loads(queryset.first().field_a1_str), ["Test", "Extra Test"]
        )

    def test_link_reversed_with_parent_links__many_to_many(self):
        satd = me_factories.SatD1Factory()
        me_factories.LinkHubCHubDFactory(hub_in=self.hubc1, hub_out=satd.hub_entity)
        repository = HubDRepositoryReversedParentLink()
        queryset = repository.receive()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(json.loads(queryset.first().field_a1_str), ["Test"])

    def test_link_with_reversed_parent(self):
        hub_c = me_factories.HubCFactory()
        sat_a = me_factories.SatA1Factory(field_a1_str="A1Test")
        me_factories.LinkHubAHubCFactory(hub_in=sat_a.hub_entity, hub_out=hub_c)
        satb = me_factories.SatB1Factory(field_b1_str="B1Test")
        me_factories.LinkHubAHubBFactory(
            hub_in=sat_a.hub_entity, hub_out=satb.hub_entity
        )
        repository = HubCRepositoryReversedParents()
        c_object = repository.receive().get(hub__pk=hub_c.pk)
        self.assertEqual(json.loads(c_object.field_a1_str), ["A1Test"])
        self.assertEqual(json.loads(c_object.field_b1_str), ["B1Test"])

    def test_link_with_reversed_parent__many_to_many__raise_no_error(self):
        hub_c = me_factories.HubCFactory()
        sat_a = me_factories.SatA1Factory(field_a1_str="A1Test")
        me_factories.LinkHubAHubCFactory(hub_in=sat_a.hub_entity, hub_out=hub_c)
        satb1 = me_factories.SatB1Factory(field_b1_str="B1Test1")
        me_factories.LinkHubAHubBFactory(
            hub_in=sat_a.hub_entity, hub_out=satb1.hub_entity
        )
        satb2 = me_factories.SatB1Factory(field_b1_str="B1Test2")
        me_factories.LinkHubAHubBFactory(
            hub_in=sat_a.hub_entity, hub_out=satb2.hub_entity
        )
        repository = HubCRepositoryReversedParents()
        test_element = repository.receive().get(hub__pk=hub_c.pk)
        test_field = json.loads(test_element.field_b1_str)
        self.assertEqual(len(test_field), 2)
        self.assertIn("B1Test1", test_field)
        self.assertIn("B1Test2", test_field)

    def test_link_with_reversed_parent__non_matching_items(self):
        def call_repo():
            return HubCRepositoryReversedParentsNoMatchingReversedParents()

        self.assertRaises(ValueError, call_repo)

    def test_link_with_many_to_many_parents(self):
        sat_e1 = me_factories.SatE1Factory(field_e1_str="Test1")
        hub_d1 = me_factories.HubDFactory(hub_e=sat_e1.hub_entity)
        sat_e2 = me_factories.SatE1Factory(field_e1_str="Test2")
        hub_d2 = me_factories.HubDFactory(hub_e=sat_e2.hub_entity)
        hub_c = me_factories.HubCFactory(hub_d=[hub_d1, hub_d2])
        repo = HubCRepositoryWithManyToManyParents({})
        test_query = repo.receive()
        test_element = test_query.get(hub_entity_id=hub_c.pk)
        self.assertCountEqual(json.loads(test_element.field_e1_str), ["Test1", "Test2"])

    def test_link_with_value_date_scope_path_restricts_to_matching_value_date(self):
        """Plain hub-level links (LinkHubCHubD, LinkHubDHubE) carry no value_date
        of their own, so without value_date_scope_path the traversal would match
        every HubD ever linked to HubC, across all value dates. With it set, each
        CHubValueDate row should only pick up the SatE1 value reachable through
        the HubD that was linked for that exact value date."""
        hub_c = me_factories.HubCFactory()
        value_dates = ["2024-01-01", "2025-01-01", "2026-01-01"]
        expected = {}
        for value_date in value_dates:
            me_factories.CHubValueDateFactory(hub=hub_c, value_date=value_date)
            sat_e1 = me_factories.SatE1Factory(field_e1_str=f"E-{value_date}")
            hub_d = me_factories.HubDFactory(hub_e=sat_e1.hub_entity)
            me_factories.LinkHubCHubDFactory(hub_in=hub_c, hub_out=hub_d)
            me_factories.DHubValueDateFactory(hub=hub_d, value_date=value_date)
            expected[value_date] = sat_e1.field_e1_str

        repo = HubCRepositoryWithValueDateScopedLink({})
        results = repo.receive().filter(hub_entity_id=hub_c.pk)
        self.assertEqual(results.count(), len(value_dates))
        for row in results:
            self.assertEqual(
                json.loads(row.field_e1_str), [expected[str(row.value_date)]]
            )

    def test_link_with_paired_json_annotation_keeps_fields_paired_per_row(self):
        """Independently JSON_AGG-ing the TS satellite field and the field from
        the secondary linked hub gives no guarantee that the database returns
        both arrays in the same row order, making positional zip() pairing on
        the consuming side unreliable. The combined annotation instead builds
        a {field: ..., extra_key: ...} JSON object per linked HubValueDate row
        at the SQL level, so pairing is guaranteed by construction."""
        hub_c = me_factories.HubCFactory()
        value_dates = ["2024-01-01", "2025-01-01", "2026-01-01"]
        expected: dict[str, list[dict[str, object]]] = {}
        for value_date in value_dates:
            me_factories.CHubValueDateFactory(hub=hub_c, value_date=value_date)

            expected[value_date] = []
            for idx, suffix in enumerate(
                ("1", "2") if value_date == value_dates[0] else ("1",)
            ):
                sat_e1 = me_factories.SatE1Factory(
                    field_e1_str=f"E-{value_date}-{suffix}"
                )
                hub_d = me_factories.HubDFactory(hub_e=sat_e1.hub_entity)
                me_factories.LinkHubCHubDFactory(hub_in=hub_c, hub_out=hub_d)
                d_hvd = me_factories.DHubValueDateFactory(
                    hub=hub_d, value_date=value_date
                )
                sat_tsd2 = me_factories.SatTSD2Factory(
                    hub_value_date=d_hvd,
                    field_tsd2_float=float(value_date[:4]),
                    field_tsd2_int=idx + 1,
                )
                expected[value_date].append(
                    {
                        "field_tsd2_float": sat_tsd2.field_tsd2_float,
                        "field_tsd2_int": sat_tsd2.field_tsd2_int,
                        "field_e1_str": sat_e1.field_e1_str,
                    }
                )

        repo = HubCRepositoryWithPairedJsonAnnotation({})
        results = repo.receive().filter(hub_entity_id=hub_c.pk)
        self.assertEqual(results.count(), len(value_dates))
        for row in results:
            details = json.loads(row.tsd2_with_e1_details)
            self.assertEqual(
                sorted(details, key=lambda d: d["field_e1_str"]),
                sorted(expected[str(row.value_date)], key=lambda d: d["field_e1_str"]),
            )

    def test_link_with_many_to_one_parents(self):
        sat_b1 = me_factories.SatB1Factory(field_b1_str="Test1")
        hub_a1 = me_factories.HubAFactory(hub_b=sat_b1.hub_entity)
        sat_b2 = me_factories.SatB1Factory(field_b1_str="Test2")
        hub_a2 = me_factories.HubAFactory(hub_b=sat_b2.hub_entity)
        hub_c = me_factories.HubCFactory(hub_a=[hub_a1, hub_a2])
        repo = HubCRepositoryWithManyToOneParents({})
        test_query = repo.receive()
        test_element = test_query.get(hub_entity_id=hub_c.pk)
        self.assertCountEqual(json.loads(test_element.field_b1_str), ["Test1", "Test2"])


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
        self.assertEqual(qs1.prev_field_tsc2_float, 1.0)
        self.assertEqual(qs1.value_date, montrek_time(2024, 11, 16).date())
        qs2 = test_query.get(field_c1_str="Bonjour")
        self.assertEqual(qs2.field_tsc2_float, 4.0)
        self.assertEqual(qs2.prev_field_tsc2_float, 2.0)
        self.assertEqual(qs2.value_date, montrek_time(2024, 11, 16).date())
        qs3 = test_query.get(field_c1_str="Hola")
        self.assertIsNone(qs3.field_tsc2_float)
        self.assertIsNone(qs3.prev_field_tsc2_float)
        self.assertIsNone(qs3.value_date)

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
        sat_d1_2 = me_factories.SatD1Factory(field_d1_int=5)
        sat_c1 = me_factories.SatC1Factory()
        sat_c1.hub_entity.link_hub_c_hub_d.add(sat_d1_1.hub_entity)
        sat_c1.hub_entity.link_hub_c_hub_d.add(sat_d1_2.hub_entity)
        sat_a2_1 = me_factories.SatA2Factory(field_a2_float=2.5)
        sat_a2_2 = me_factories.SatA2Factory(field_a2_float=3.0)
        sat_a2_3 = me_factories.SatA2Factory(field_a2_float=None)
        sat_a2_1.hub_entity.link_hub_a_hub_c.add(sat_c1.hub_entity)
        sat_a2_2.hub_entity.link_hub_a_hub_c.add(sat_c1.hub_entity)
        sat_a2_3.hub_entity.link_hub_a_hub_c.add(sat_c1.hub_entity)

    def test_latest_entry(self):
        repo = HubCRepositoryLast()
        test_query = repo.receive()
        self.assertEqual(test_query.count(), 1)
        self.assertEqual(test_query[0].field_d1_int, 2)

    def test_mean(self):
        repo = HubCRepositoryMean()
        test_query = repo.receive()
        self.assertEqual(test_query.count(), 1)
        self.assertEqual(test_query[0].field_d1_int, 3.5)
        self.assertAlmostEqual(test_query[0].field_a2_float, 2.75, delta=0.01)

    def test_count(self):
        repo = HubCRepositoryCount()
        test_query = repo.receive()
        self.assertEqual(test_query.count(), 1)
        self.assertEqual(test_query[0].field_d1_int, 2)
        self.assertEqual(test_query[0].a2_counter, 2)
        self.assertEqual(test_query[0].a2_counter_w_filter, 1)


class TestTSAggFuncs(TestCase):
    def setUp(self) -> None:
        self.test_date_1 = "2026-04-20"
        self.test_date_2 = "2026-04-21"
        sat_d1 = me_factories.SatD1Factory()

        self.hvd_1 = me_factories.DHubValueDateFactory(
            hub=sat_d1.hub_entity, value_date=self.test_date_1
        )
        self.hvd_2 = me_factories.DHubValueDateFactory(
            hub=sat_d1.hub_entity, value_date=self.test_date_2
        )
        tsc2_sats = (
            me_factories.SatTSC2Factory(
                field_tsc2_float=2.5, value_date=self.test_date_1
            ),
            me_factories.SatTSC2Factory(
                field_tsc2_float=3.5, value_date=self.test_date_1
            ),
            me_factories.SatTSC2Factory(
                field_tsc2_float=4.5, value_date=self.test_date_2
            ),
        )
        for sat in tsc2_sats:
            sat.hub_value_date.hub.link_hub_c_hub_d.add(sat_d1.hub_entity)

    def test_sum(self):
        repo = HubDTSLinkAggRepositorySum()
        test_query = repo.receive()
        first_entry = test_query.get(pk=self.hvd_1.pk)
        second_entry = test_query.get(pk=self.hvd_2.pk)
        self.assertEqual(first_entry.field_tsc2_float, 6)
        self.assertEqual(second_entry.field_tsc2_float, 4.5)

    def test_link_hub_value_date_filter_decouples_linked_value_date_from_outer_row(
        self,
    ):
        """With latest_ts=True, the outer row is the HubD HVD at test_date_2.
        The default-dated annotation aggregates linked SatTSC2 values at the
        same value date as the outer row (test_date_2: just 4.5), while
        link_hub_value_date_filter pins the second annotation to test_date_1
        (2.5 and 3.5, mean 3.0) regardless of the outer row's value date."""
        repo = HubDTSLinkAggRepositoryWithLinkHubValueDateFilter(
            {"prev_value_date": self.test_date_1}
        )
        test_query = repo.receive()
        self.assertEqual(test_query.count(), 1)
        entry = test_query.get()
        self.assertEqual(entry.field_tsc2_float, 4.5)
        self.assertAlmostEqual(entry.prev_field_tsc2_float, 3.0)

    def test_link_hub_value_date_filter_with_sum_pins_aggregation_to_explicit_date(
        self,
    ):
        """agg_func="sum" combined with link_hub_value_date_filter sums the
        linked SatTSC2 values across all linked HubC hubs at the pinned
        value date (test_date_1: 2.5 + 3.5 = 6.0), excluding the linked
        hub's value at test_date_2 (4.5), regardless of the outer row's own
        value date."""
        repo = HubDTSLinkAggRepositoryWithLinkHubValueDateFilter(
            {"prev_value_date": self.test_date_1}
        )
        test_query = repo.receive()
        entry = test_query.get()
        self.assertAlmostEqual(entry.prev_field_tsc2_float_sum, 6.0)


class TestStaticAggFuncsAll(TestCase):
    """Tests for agg_func="all": True iff every linked non-NULL value is truthy; NULL values are ignored (treated as not applicable)."""

    def _hub_c_with_d1s(self, *int_values):
        sat_c1 = me_factories.SatC1Factory()
        for val in int_values:
            sat_d1 = me_factories.SatD1Factory(field_d1_int=val)
            sat_c1.hub_entity.link_hub_c_hub_d.add(sat_d1.hub_entity)
        return sat_c1

    def _hub_c_with_a2s(self, *float_values):
        sat_c1 = me_factories.SatC1Factory()
        for val in float_values:
            sat_a2 = me_factories.SatA2Factory(field_a2_float=val)
            sat_a2.hub_entity.link_hub_a_hub_c.add(sat_c1.hub_entity)
        return sat_c1

    def test_all_true_when_all_direct_link_values_are_truthy(self):
        self._hub_c_with_d1s(1, 2)
        repo = HubCRepositoryAll()
        result = repo.receive()
        self.assertEqual(result.count(), 1)
        self.assertTrue(result[0].field_d1_int)

    def test_all_false_when_one_direct_link_value_is_zero(self):
        self._hub_c_with_d1s(1, 0)
        repo = HubCRepositoryAll()
        result = repo.receive()
        self.assertEqual(result.count(), 1)
        self.assertFalse(result[0].field_d1_int)

    def test_all_false_when_all_direct_link_values_are_zero(self):
        self._hub_c_with_d1s(0, 0)
        repo = HubCRepositoryAll()
        result = repo.receive()
        self.assertEqual(result.count(), 1)
        self.assertFalse(result[0].field_d1_int)

    def test_all_true_reversed_link_when_all_values_are_truthy(self):
        self._hub_c_with_a2s(2.5, 3.0)
        repo = HubCRepositoryAll()
        result = repo.receive()
        self.assertEqual(result.count(), 1)
        self.assertTrue(result[0].field_a2_float)

    def test_all_true_reversed_link_when_one_value_is_none(self):
        # NULL is skipped (treated as not-applicable, like SQL aggregate NULL handling),
        # so all([truthy, NULL]) is still True.
        self._hub_c_with_a2s(2.5, None)
        repo = HubCRepositoryAll()
        result = repo.receive()
        self.assertEqual(result.count(), 1)
        self.assertTrue(result[0].field_a2_float)

    def test_all_false_reversed_link_when_one_value_is_zero(self):
        self._hub_c_with_a2s(2.5, 0.0)
        repo = HubCRepositoryAll()
        result = repo.receive()
        self.assertEqual(result.count(), 1)
        self.assertFalse(result[0].field_a2_float)

    def test_multiple_hubs_each_evaluated_independently(self):
        """Two HubC objects: one with all-truthy links, one with a falsy link."""
        self._hub_c_with_d1s(1, 2)
        self._hub_c_with_d1s(1, 0)
        repo = HubCRepositoryAll()
        result = repo.receive().order_by("pk")
        self.assertEqual(result.count(), 2)
        self.assertTrue(result[0].field_d1_int)
        self.assertFalse(result[1].field_d1_int)


class TestTimeSeriesPerformance(TestCase):
    def test_large_datasets_with_filter__performance(self):
        year_range = range(2010, 2021)
        hubs = me_factories.HubCFactory.create_batch(1000)
        sat_tsc2 = []
        sat_tsc3 = []
        value_date_lists = {
            year: ValueDateListFactory(value_date=montrek_time(year, 1, 1))
            for year in year_range
        }
        for hub in hubs:
            me_factories.SatC1Factory.create(hub_entity=hub)
            for year in year_range:
                hvd = me_factories.CHubValueDateFactory.create(
                    hub=hub, value_date_list=value_date_lists[year]
                )
                sat_tsc2.append(
                    me_models.SatTSC2(
                        hub_value_date=hvd, value_date=hvd.value_date_list.value_date
                    )
                )
                sat_tsc3.append(
                    me_models.SatTSC3(
                        hub_value_date=hvd, value_date=hvd.value_date_list.value_date
                    )
                )
        me_models.SatTSC2.objects.bulk_create(sat_tsc2, batch_size=1000)
        me_models.SatTSC3.objects.bulk_create(sat_tsc3, batch_size=1000)
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
        self.assertCountEqual(
            json.loads(satd_queryset[0].hub_b_id),
            [self.satb1.hub_entity_id, self.satb2.hub_entity_id],
        )
        self.assertCountEqual(
            json.loads(satd_queryset[0].field_b1_str),
            [self.satb1.field_b1_str, self.satb2.field_b1_str],
        )
        self.assertEqual(
            json.loads(satd_queryset[1].field_b1_str), [self.satb1.field_b1_str]
        )

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
        repository_b.store_in_view_model()
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

    def test_remove_existing_links(self):
        me_factories.SatD1Factory(
            field_d1_str="dritter",
            field_d1_int=3,
        )
        me_factories.SatD1Factory(
            field_d1_str="vierter",
            field_d1_int=4,
        )
        hub_entity_id = self.satb1.hub_entity_id

        input_data = {
            "hub_entity_id": hub_entity_id,
            "link_hub_b_hub_d": [],
        }
        repository_b = HubBRepository(session_data={"user_id": self.user.id})
        repository_b.store_in_view_model()
        repository_b.std_create_object(input_data)

        hub_b = repository_b.receive().filter(hub__id=hub_entity_id).first()

        links = me_models.LinkHubBHubD.objects.filter(hub_in=hub_b.hub.id).all()

        self.assertIsNone(hub_b.field_d1_str)
        for link in links:
            self.assertEqual(link.state_date_start, MIN_DATE)
            self.assertLess(link.state_date_end, MAX_DATE)

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
                expected_value in repo_c_static_satellite_fields
                for expected_value in expected_values
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
                expected_value in repo_c_time_series_satellite_fields
                for expected_value in expected_values
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
        self.assertEqual(json.loads(query.first().field_d1_str), [d_sat1.field_d1_str])

    def test_json_agg_field_type(self):
        annotator = HubCRepository({}).annotator
        field_map = annotator.get_annotated_field_map()
        self.assertIsInstance(field_map["hub_d_id"], models.CharField)
        self.assertIsInstance(field_map["field_d1_int"], models.IntegerField)
        self.assertIsInstance(field_map["field_tsd2_float_agg"], models.FloatField)

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
        self.assertCountEqual(
            json.loads(query.first().field_d1_str),
            [d_sat1.field_d1_str, d_sat2.field_d1_str],
        )
        self.assertEqual(query.last().field_c1_str, c_sat2.field_c1_str)
        self.assertEqual(json.loads(query.last().field_d1_str), [d_sat1.field_d1_str])

    def test_ts_satellite_concept__multiple_ts_links_aggregated_to_one(self):
        c_sat1 = me_factories.SatC1Factory()
        tsd2_fac1 = me_factories.SatTSD2Factory(
            field_tsd2_float=10, value_date="2019-09-09"
        )
        me_factories.SatTSD2Factory(
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
        self.assertEqual(json.loads(test_obj.comment_tsd2), ["Third Comment"])
        self.assertEqual(json.loads(test_obj.comment_d1), ["Fourth Comment"])
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


class TestRepositoryViewModel(TestCase):
    def setUp(self) -> None:
        self.user = MontrekUserFactory()
        self.repo = HubARepository({"user_id": self.user.id})

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

    def test_call_view_model_a_day_after_creation(self):
        with freeze_time("2023-01-01") as frozen_date:
            self.repo.view_model.reference_date = datetime.date(2023, 1, 1)
            # Check that View Model data is called when reference_dates are inline
            with patch.object(HubARepository, "get_view_model_query") as mock_method:
                self.repo.receive()
                mock_method.assert_called()
            # Check that this still the case one day after
            frozen_date.tick(delta=datetime.timedelta(days=1))
            repo = HubARepository({"user_id": self.user.id})
            with patch.object(HubARepository, "get_view_model_query") as mock_method:
                repo.receive()
                mock_method.assert_called()

    def test_dont_call_view_model_when_reference_date_call_is_done(self):
        repo = HubARepository({"user_id": self.user.id, "reference_date": "2023-01-01"})
        with patch.object(HubARepository, "get_view_model_query") as mock_method:
            repo.receive()
            mock_method.assert_not_called()

    def test_view_model_with_filter(self):
        me_factories.SatA1Factory.create(field_a1_str="Test")
        me_factories.SatA1Factory.create(field_a1_str="Test2")
        me_factories.SatA1Factory.create(field_a1_str="Test3")
        filter_data = {
            "request_path": "test_path",
            "filter": {
                "test_path": {
                    "field_a1_str": {
                        "filter_value": "Test",
                        "filter_negate": False,
                    }
                }
            },
        }
        repo = HubARepository(session_data=filter_data)
        repo.store_in_view_model()
        query = repo.get_view_model_query()
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().field_a1_str, "Test")

    def test_view_model_with_filter__filter_not_applied(self):
        me_factories.SatA1Factory.create(field_a1_str="Test")
        me_factories.SatA1Factory.create(field_a1_str="Test2")
        me_factories.SatA1Factory.create(field_a1_str="Test3")
        filter_data = {
            "request_path": "test_path",
            "filter": {
                "test_path": {
                    "field_a1_str": {
                        "filter_value": "Test",
                        "filter_negate": False,
                    }
                }
            },
        }
        repo = HubARepository(session_data=filter_data)
        repo.store_in_view_model()
        query = repo.get_view_model_query(apply_filter=False)
        self.assertEqual(query.count(), 3)

    def test_create_object_from_dict_with_view_model(self):
        self.repo.create_by_dict({"field_a1_str": "Hallo", "field_a1_int": 15})
        objects = self.repo.receive()
        created_object = objects.first()
        self.assertEqual(objects.count(), 1)
        self.assertEqual(created_object.field_a1_str, "Hallo")
        self.assertEqual(created_object.field_a1_int, 15)

        self.repo.create_by_dict({"field_a1_str": "Hallo", "field_a1_int": 16})
        objects = self.repo.receive()
        created_object = objects.first()
        self.assertEqual(objects.count(), 1)
        self.assertEqual(created_object.field_a1_str, "Hallo")
        self.assertEqual(created_object.field_a1_int, 16)

    def test_delete_object_from_view_model(self):
        me_factories.SatA1Factory.create(field_a1_str="Test")
        me_factories.SatA1Factory.create(field_a1_str="Test2")
        me_factories.SatA1Factory.create(field_a1_str="Test3")

        self.repo.store_in_view_model()
        object_to_delete = self.repo.receive().get(field_a1_str="Test")
        self.repo.delete(object_to_delete.hub)
        test_objects = self.repo.receive()
        self.assertEqual(test_objects.count(), 2)
        field_a1_strs = test_objects.values_list("field_a1_str", flat=True)
        self.assertIn("Test2", field_a1_strs)
        self.assertIn("Test3", field_a1_strs)
        self.assertNotIn("Test", field_a1_strs)

    def test_delete_object_from_view_model_ts(self):
        repo = HubCRepositoryViewModel()
        hub = me_factories.HubCFactory()
        hub_vd1 = me_factories.CHubValueDateFactory(hub=hub, value_date="2025-10-17")
        me_factories.SatTSC2Factory(field_tsc2_float=1.0, hub_value_date=hub_vd1)
        hub_vd2 = me_factories.CHubValueDateFactory(hub=hub, value_date="2025-10-18")
        me_factories.SatTSC2Factory(field_tsc2_float=2.0, hub_value_date=hub_vd2)
        hub_vd3 = me_factories.CHubValueDateFactory(hub=hub, value_date="2025-10-19")
        me_factories.SatTSC2Factory(field_tsc2_float=3.0, hub_value_date=hub_vd3)
        repo.store_in_view_model()
        prior_objs = repo.receive()
        self.assertEqual(prior_objs.count(), 3)
        repo.delete(hub)
        post_objs = repo.receive()
        self.assertEqual(post_objs.count(), 0)


class TestRepositoryAsDF(TestCase):
    def setUp(self):
        sats = me_factories.SatA1Factory.create_batch(5)
        for sat in sats:
            me_factories.SatA2Factory.create(hub_entity=sat.hub_entity)
            me_factories.SatB1Factory.create(link_a=sat)

    def test_get_repository_dtypes(self):
        for repo, expected_result in (
            (
                HubARepository,
                {
                    "value_date": "datetime64[ns]",
                    "hub_entity_id": "Int64",
                    "created_at": "datetime64[ns, UTC]",
                    "created_by": "string",
                    "comment": "string",
                    "field_a1_int": "Int64",
                    "field_a1_str": "string",
                    "field_a2_float": "float64",
                    "field_a2_str": "string",
                    "field_b1_str": "string",
                    "field_b1_date": "datetime64[ns]",
                },
            ),
            (
                HubBRepository,
                {
                    "alert_level": "category",
                    "alert_message": "string",
                    "comment": "string",
                    "created_at": "datetime64[ns, UTC]",
                    "created_by": "string",
                    "field_b1_date": "datetime64[ns]",
                    "field_b1_str": "string",
                    "field_b2_choice": "category",
                    "field_b2_str": "string",
                    "field_d1_int": "string",
                    "field_d1_str": "string",
                    "hub_d_id": "string",
                    "hub_entity_id": "Int64",
                    "value_date": "datetime64[ns]",
                },
            ),
            (
                HubARepository5,
                {
                    "comment": "string",
                    "created_at": "datetime64[ns, UTC]",
                    "created_by": "string",
                    "field_a5_str": "string",
                    "hub_entity_id": "Int64",
                    "secret_field": "string",
                    "value_date": "datetime64[ns]",
                },
            ),
        ):
            with self.subTest(f"dtypes for {repo}"):
                dtypes = repo({}).get_df_dtypes()
                self.assertEqual(dtypes, expected_result)

    def test_get_df(self):
        repo = HubARepository({})
        repo.store_in_view_model()
        test_df = repo.get_df()
        self.assertEqual(test_df.shape, (5, 13))

    def test_get_df_selected_columns(self):
        repo = HubARepository({})
        repo.store_in_view_model()
        test_df = repo.get_df(columns=["field_a1_str", "field_a2_float"])
        self.assertEqual(test_df.shape, (5, 2))

    def test_get_df_no_category_columns(self):
        repo = HubBRepository({})
        df = repo.get_df(no_category_columns=["alert_level"])
        self.assertEqual(df["alert_level"].dtype, "string")

    def test_get_df_dtypes(self):
        repo = HubARepository({})
        repo.store_in_view_model()
        df = repo.get_df()
        # integers
        self.assertTrue(
            pd.api.types.is_integer_dtype(df["id"]),
            "id should be an integer dtype",
        )
        self.assertTrue(
            pd.api.types.is_integer_dtype(df["field_a1_int"]),
            "field_a1_int should be an integer dtype",
        )
        self.assertTrue(
            pd.api.types.is_integer_dtype(df["hub_entity_id"]),
            "hub_entity_id should be an integer dtype",
        )

        # floats
        self.assertTrue(
            pd.api.types.is_float_dtype(df["field_a2_float"]),
            "field_a2_float should be a float dtype",
        )

        # strings
        for col in [
            "field_a1_str",
            "field_a2_str",
            "field_b1_str",
            "created_by",
            "comment",
        ]:
            self.assertTrue(
                pd.api.types.is_string_dtype(df[col]),
                f"{col} should be a string dtype",
            )

        # datetimes (naive)
        for col in ["field_b1_date", "value_date"]:
            self.assertTrue(
                pd.api.types.is_datetime64_ns_dtype(df[col]),
                f"{col} should be a naive datetime64[ns]",
            )

        # datetime (tz-aware)
        self.assertTrue(
            pd.api.types.is_datetime64tz_dtype(df["created_at"]),
            "created_at should be timezone-aware",
        )
        self.assertEqual(
            str(df["created_at"].dtype.tz),
            "UTC",
            "created_at should be in UTC",
        )

    def test_ts_df(self):
        me_factories.SatTSC2Factory(value_date="2023-12-24")
        me_factories.SatTSC2Factory(value_date="2024-12-24")
        repo = HubCRepository()
        df = repo.get_df()
        self.assertIn("value_date", df.columns)

    def test_get_df_empty(self):
        repo = HubARepository({})

        # Force empty result
        df = repo.get_df()
        df = df.iloc[0:0]

        df2 = repo._apply_category_dtype(df)

        self.assertEqual(len(df2), 0)
        self.assertEqual(df2.dtypes.to_dict(), df.dtypes.to_dict())

    def test_all_null_string_not_category(self):
        repo = HubARepository({})
        repo.store_in_view_model()
        df = repo.get_df()

        df["comment"] = None  # force all-null string column

        df2 = repo._apply_category_dtype(df)

        self.assertFalse(
            pd.api.types.is_categorical_dtype(df2["comment"]),
            "all-null column must not become category",
        )

    def test_ratio_threshold_respected(self):
        repo = HubARepository({})
        repo.store_in_view_model()
        df = repo.get_df()

        # Expand to N=100
        df = pd.concat([df] * 20, ignore_index=True)

        # 20 unique values → ratio = 0.20
        df["field_a2_str"] = [f"v{i % 20}" for i in range(len(df))]

        df2 = repo._apply_category_dtype(df, threshold=0.10)

        self.assertTrue(
            pd.api.types.is_string_dtype(df2["field_a2_str"]),
            "high-ratio string column must remain string",
        )

    def test_choices_always_category(self):
        repo = HubBRepository({})
        repo.store_in_view_model()
        df = repo.get_df()

        self.assertTrue(
            pd.api.types.is_categorical_dtype(df["field_b2_choice"]),
            "choices field must always be category",
        )

    def test_datetime_timezone_preserved(self):
        repo = HubARepository({})
        repo.store_in_view_model()
        df = repo.get_df()

        self.assertTrue(pd.api.types.is_datetime64tz_dtype(df["created_at"]))
        self.assertEqual(str(df["created_at"].dtype.tz), "UTC")

    def test_free_text_never_category(self):
        repo = HubARepository({})
        repo.store_in_view_model()
        df = repo.get_df()

        df["comment"] = [f"text {i}" for i in range(len(df))]

        df2 = repo._apply_category_dtype(df)

        self.assertTrue(
            pd.api.types.is_string_dtype(df2["comment"]),
            "free text must not be converted to category",
        )

    def test_convert_min_dates(self):
        sat = me_factories.SatA1Factory.create()
        me_factories.SatA2Factory.create(hub_entity=sat.hub_entity)
        sat_b1 = me_factories.SatB1Factory.create(
            link_a=sat, field_b1_date=datetime.date.min
        )
        repo = HubBRepository({})
        repo.store_in_view_model()
        df = repo.get_df()
        field_b1_date = df.loc[df["id"] == sat_b1.hub_entity_id, "field_b1_date"].iloc[
            0
        ]
        self.assertEqual(
            field_b1_date.date(),
            datetime.date(1677, 9, 22),
        )


class TestReceiveWithAliases(TestCase):
    def test_simple_receive_statement(self):
        """
        When a repository has satellites attached which have a field identifier and the hub entity as identifier field,
        the right hub entity has to be found
        """
        hubs = me_factories.HubAFactory.create_batch(2)
        me_factories.SatA1Factory(
            hub_entity=hubs[0], field_a1_str="test_1", field_a1_int=1
        )
        me_factories.SatA1Factory(
            hub_entity=hubs[1], field_a1_str="test_2", field_a1_int=2
        )
        me_factories.SatA2Factory(hub_entity=hubs[0], field_a2_str="A2 1")
        me_factories.SatA2Factory(hub_entity=hubs[1], field_a2_str="A2 2")
        repository = HubARepository()
        repository.store_in_view_model()
        test_query = repository.receive()
        self.assertEqual(test_query.count(), 2)
        self.assertEqual(test_query[0].field_a1_str, "test_1")
        self.assertEqual(test_query[1].field_a1_str, "test_2")
        self.assertEqual(test_query[0].field_a2_str, "A2 1")
        self.assertEqual(test_query[1].field_a2_str, "A2 2")


class TestCrossSatelliteFilter(TestCase):
    """Tests for the cross_satellite_filters parameter of add_linked_satellites_field_annotations.

    Model structure used:
        HubB --LinkHubBHubD--> HubD --SatD1 (fetched field)
                                   \\
                                    <--LinkHubCHubD-- HubC --SatC1 (cross filter)

    HubBRepositoryWithCrossSatFilter fetches SatD1.field_d1_str but only for HubDs
    that have a linked HubC (via LinkHubCHubD reversed) with SatC1.field_c1_str == "matched".
    """

    def _make_hub_b_with_matching_hub_d(self, b1_str: str, d1_str: str):
        """Create a HubB → HubD link where HubD has a matching SatC1 via HubC."""
        satb = me_factories.SatB1Factory(field_b1_str=b1_str)
        satd = me_factories.SatD1Factory(field_d1_str=d1_str)
        me_factories.LinkHubBHubDFactory(
            hub_in=satb.hub_entity, hub_out=satd.hub_entity
        )
        hubc = me_factories.HubCFactory()
        me_factories.SatC1Factory(hub_entity=hubc, field_c1_str="matched")
        me_factories.LinkHubCHubDFactory(hub_in=hubc, hub_out=satd.hub_entity)
        return satb, satd

    def _make_hub_b_with_non_matching_hub_d(self, b1_str: str, d1_str: str):
        """Create a HubB → HubD link where HubD has no SatC1 with field_c1_str='matched'."""
        satb = me_factories.SatB1Factory(field_b1_str=b1_str)
        satd = me_factories.SatD1Factory(field_d1_str=d1_str)
        me_factories.LinkHubBHubDFactory(
            hub_in=satb.hub_entity, hub_out=satd.hub_entity
        )
        return satb, satd

    def test_matching_hub_d_returns_field_value(self):
        satb, _ = self._make_hub_b_with_matching_hub_d("B-match", "D-match")
        repo = HubBRepositoryWithCrossSatFilter()
        queryset = repo.receive().filter(hub=satb.hub_entity)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(json.loads(queryset[0].field_d1_str), ["D-match"])

    def test_non_matching_hub_d_returns_none(self):
        """HubD has a HubC link but SatC1.field_c1_str does not match."""
        satb, satd = self._make_hub_b_with_non_matching_hub_d(
            "B-no-match", "D-no-match"
        )
        hubc = me_factories.HubCFactory()
        me_factories.SatC1Factory(hub_entity=hubc, field_c1_str="wrong-value")
        me_factories.LinkHubCHubDFactory(hub_in=hubc, hub_out=satd.hub_entity)

        repo = HubBRepositoryWithCrossSatFilter()
        queryset = repo.receive().filter(hub=satb.hub_entity)
        self.assertEqual(queryset.count(), 1)
        self.assertIsNone(queryset[0].field_d1_str)

    def test_hub_d_with_no_cross_link_returns_none(self):
        """HubD has no HubC link at all — cross filter excludes it."""
        satb, _ = self._make_hub_b_with_non_matching_hub_d("B-no-link", "D-no-link")
        repo = HubBRepositoryWithCrossSatFilter()
        queryset = repo.receive().filter(hub=satb.hub_entity)
        self.assertEqual(queryset.count(), 1)
        self.assertIsNone(queryset[0].field_d1_str)

    def test_mixed_hub_bs_only_matching_gets_value(self):
        """Two HubBs: one with a matching HubD, one without."""
        self._make_hub_b_with_matching_hub_d("B1", "D1-match")
        self._make_hub_b_with_non_matching_hub_d("B2", "D2-no-match")

        repo = HubBRepositoryWithCrossSatFilter()
        queryset = repo.receive().order_by("field_b1_str")
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(json.loads(queryset[0].field_d1_str), ["D1-match"])
        self.assertIsNone(queryset[1].field_d1_str)

    def test_cross_satellite_filter_with_count_agg(self):
        """Count aggregation respects the cross-satellite filter."""

        class HubBCountCrossSatFilter(MontrekRepository):
            hub_class = me_models.HubB

            def set_annotations(self):
                self.add_linked_satellites_field_annotations(
                    me_models.SatD1,
                    me_models.LinkHubBHubD,
                    ["field_d1_str"],
                    agg_func="count",
                    cross_satellite_filters=(
                        CrossSatelliteFilter(
                            satellite_class=me_models.SatC1,
                            link_class=me_models.LinkHubCHubD,
                            filter_dict={"field_c1_str": "matched"},
                            reversed_link=True,
                        ),
                    ),
                )

        satb, _ = self._make_hub_b_with_matching_hub_d("B-count", "D-count")
        # Add a second matching HubD to the same HubB
        satd2 = me_factories.SatD1Factory(field_d1_str="D-count-2")
        me_factories.LinkHubBHubDFactory(
            hub_in=satb.hub_entity, hub_out=satd2.hub_entity
        )
        hubc2 = me_factories.HubCFactory()
        me_factories.SatC1Factory(hub_entity=hubc2, field_c1_str="matched")
        me_factories.LinkHubCHubDFactory(hub_in=hubc2, hub_out=satd2.hub_entity)

        # Also add a non-matching HubD linked to the same HubB — should NOT be counted
        satd3 = me_factories.SatD1Factory(field_d1_str="D-count-3")
        me_factories.LinkHubBHubDFactory(
            hub_in=satb.hub_entity, hub_out=satd3.hub_entity
        )

        repo = HubBCountCrossSatFilter()
        queryset = repo.receive().filter(hub=satb.hub_entity)
        self.assertEqual(queryset.count(), 1)
        # Only the 2 matching HubDs are counted, the non-matching one is excluded
        self.assertEqual(int(queryset[0].field_d1_str), 2)

    def test_cross_satellite_filter_reversed_link_false(self):
        """Test with reversed_link=False: filter on a satellite reached via hub_out.

        HubA --LinkHubAHubB (hub_in=HubA, hub_out=HubB)--> HubB --SatB1 (fetched)
        Cross filter: HubB --LinkHubBHubD (hub_in=HubB, hub_out=HubD)--> HubD --SatD1
        Only HubBs where the linked HubD has SatD1.field_d1_int >= 5 are included.
        """

        class HubARepositoryWithCrossSatFilter(MontrekRepository):
            hub_class = me_models.HubA

            def set_annotations(self):
                self.add_linked_satellites_field_annotations(
                    me_models.SatB1,
                    me_models.LinkHubAHubB,
                    ["field_b1_str"],
                    cross_satellite_filters=(
                        CrossSatelliteFilter(
                            satellite_class=me_models.SatD1,
                            link_class=me_models.LinkHubBHubD,
                            filter_dict={"field_d1_int__gte": 5},
                            reversed_link=False,
                        ),
                    ),
                )

        # HubA1 → HubB1 → HubD1 (field_d1_int=10, passes filter)
        huba1 = me_factories.HubAFactory()
        satb1 = me_factories.SatB1Factory(field_b1_str="B-pass")
        me_factories.LinkHubAHubBFactory(hub_in=huba1, hub_out=satb1.hub_entity)
        satd1 = me_factories.SatD1Factory(field_d1_int=10)
        me_factories.LinkHubBHubDFactory(
            hub_in=satb1.hub_entity, hub_out=satd1.hub_entity
        )

        # HubA2 → HubB2 → HubD2 (field_d1_int=3, fails filter)
        huba2 = me_factories.HubAFactory()
        satb2 = me_factories.SatB1Factory(field_b1_str="B-fail")
        me_factories.LinkHubAHubBFactory(hub_in=huba2, hub_out=satb2.hub_entity)
        satd2 = me_factories.SatD1Factory(field_d1_int=3)
        me_factories.LinkHubBHubDFactory(
            hub_in=satb2.hub_entity, hub_out=satd2.hub_entity
        )

        repo = HubARepositoryWithCrossSatFilter()
        queryset = repo.receive().order_by("hub_entity_id")
        self.assertEqual(queryset.count(), 2)
        self.assertEqual(queryset[0].field_b1_str, "B-pass")
        self.assertIsNone(queryset[1].field_b1_str)

    def test_cross_satellite_filter_with_ts_cross_satellite_matching(self):
        """Cross-satellite is a timeseries satellite — matching case.

        HubB → HubD (SatD1 fetched) cross-filtered via LinkHubCHubD by SatTSC2 on HubC.
        The ORM path from SatD1's hub (HubD) to SatTSC2 on HubC is:
            hub_entity__linkhubchubd__hub_in__hub_value_date__sattsc2__field_tsc2_float

        (hub_in because reversed_link=True: HubD is hub_out in LinkHubCHubD)
        """

        class HubBRepositoryWithTSCrossSatFilter(MontrekRepository):
            hub_class = me_models.HubB

            def set_annotations(self):
                self.add_linked_satellites_field_annotations(
                    me_models.SatD1,
                    me_models.LinkHubBHubD,
                    ["field_d1_str"],
                    cross_satellite_filters=(
                        CrossSatelliteFilter(
                            satellite_class=me_models.SatTSC2,
                            link_class=me_models.LinkHubCHubD,
                            filter_dict={"field_tsc2_float__gte": 5.0},
                            reversed_link=True,
                        ),
                    ),
                )

        # HubB1 → HubD1 linked to HubC1 (SatTSC2 field_tsc2_float=10.0 → passes)
        satb1 = me_factories.SatB1Factory(field_b1_str="B-ts-pass")
        satd1 = me_factories.SatD1Factory(field_d1_str="D1-ts-match")
        me_factories.LinkHubBHubDFactory(
            hub_in=satb1.hub_entity, hub_out=satd1.hub_entity
        )
        chvd1 = me_factories.CHubValueDateFactory(hub=me_factories.HubCFactory())
        me_factories.SatTSC2Factory(hub_value_date=chvd1, field_tsc2_float=10.0)
        me_factories.LinkHubCHubDFactory(hub_in=chvd1.hub, hub_out=satd1.hub_entity)

        repo = HubBRepositoryWithTSCrossSatFilter()
        queryset = repo.receive().filter(hub=satb1.hub_entity)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(json.loads(queryset[0].field_d1_str), ["D1-ts-match"])

    def test_cross_satellite_filter_with_ts_cross_satellite_not_matching(self):
        """Cross-satellite is a timeseries satellite — non-matching case returns None."""

        class HubBRepositoryWithTSCrossSatFilter(MontrekRepository):
            hub_class = me_models.HubB

            def set_annotations(self):
                self.add_linked_satellites_field_annotations(
                    me_models.SatD1,
                    me_models.LinkHubBHubD,
                    ["field_d1_str"],
                    cross_satellite_filters=(
                        CrossSatelliteFilter(
                            satellite_class=me_models.SatTSC2,
                            link_class=me_models.LinkHubCHubD,
                            filter_dict={"field_tsc2_float__gte": 5.0},
                            reversed_link=True,
                        ),
                    ),
                )

        # HubB2 → HubD2 linked to HubC2 (SatTSC2 field_tsc2_float=2.0 → fails filter)
        satb2 = me_factories.SatB1Factory(field_b1_str="B-ts-fail")
        satd2 = me_factories.SatD1Factory(field_d1_str="D2-ts-no-match")
        me_factories.LinkHubBHubDFactory(
            hub_in=satb2.hub_entity, hub_out=satd2.hub_entity
        )
        chvd2 = me_factories.CHubValueDateFactory(hub=me_factories.HubCFactory())
        me_factories.SatTSC2Factory(hub_value_date=chvd2, field_tsc2_float=2.0)
        me_factories.LinkHubCHubDFactory(hub_in=chvd2.hub, hub_out=satd2.hub_entity)

        repo = HubBRepositoryWithTSCrossSatFilter()
        queryset = repo.receive().filter(hub=satb2.hub_entity)
        self.assertEqual(queryset.count(), 1)
        self.assertIsNone(queryset[0].field_d1_str)


class TestFilterByLinkedHub(TestCase):
    """Tests for MontrekRepository.filter_by_linked_hub.

    Uses LinkHubBHubD (hub_in=HubB, hub_out=HubD) as a concrete link so the
    tests stay within the example app.

    Forward direction (reversed_link=False):
        HubBRepository rows filtered by a specific HubD  →  hub_out is the target.

    Reversed direction (reversed_link=True):
        HubDRepository rows filtered by a specific HubB  →  hub_in is the target.
    """

    def setUp(self):
        self.satb1 = me_factories.SatB1Factory()
        self.satb2 = me_factories.SatB1Factory()
        self.satb_unlinked = me_factories.SatB1Factory()

        self.satd1 = me_factories.SatD1Factory()
        self.satd2 = me_factories.SatD1Factory()

        me_factories.LinkHubBHubDFactory.create(
            hub_in=self.satb1.hub_entity,
            hub_out=self.satd1.hub_entity,
        )
        me_factories.LinkHubBHubDFactory.create(
            hub_in=self.satb2.hub_entity,
            hub_out=self.satd2.hub_entity,
        )
        # satb_unlinked has no link to any HubD
        # Passing reference_date bypasses the view model so the annotated
        # queryset is built fresh against the in-transaction test data.
        self.ref = timezone.now()

    def _hub_b_repo(self):
        return HubBRepository({"reference_date": self.ref})

    # ------------------------------------------------------------------
    # Forward direction: filter HubB rows by HubD (hub_out)
    # ------------------------------------------------------------------

    def test_forward_link__returns_only_linked_row(self):
        """Only the HubB linked to hub_d1 should be returned."""
        repo = self._hub_b_repo()
        qs = repo.filter_by_linked_hub(
            repo.receive(), me_models.LinkHubBHubD, self.satd1.hub_entity
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].hub, self.satb1.hub_entity)

    def test_forward_link__excludes_unlinked_row(self):
        """HubB with no link to hub_d1 must not appear."""
        repo = self._hub_b_repo()
        qs = repo.filter_by_linked_hub(
            repo.receive(), me_models.LinkHubBHubD, self.satd1.hub_entity
        )
        hub_ids = list(qs.values_list("hub_id", flat=True))
        self.assertNotIn(self.satb_unlinked.hub_entity_id, hub_ids)

    def test_forward_link__excludes_row_linked_to_different_target(self):
        """HubB linked to hub_d2 must not appear when filtering by hub_d1."""
        repo = self._hub_b_repo()
        qs = repo.filter_by_linked_hub(
            repo.receive(), me_models.LinkHubBHubD, self.satd1.hub_entity
        )
        hub_ids = list(qs.values_list("hub_id", flat=True))
        self.assertNotIn(self.satb2.hub_entity_id, hub_ids)

    def test_forward_link__expired_link_is_excluded(self):
        """A link whose state_date_end lies in the past must not match."""
        hub_b_expired = me_factories.SatB1Factory().hub_entity
        me_factories.LinkHubBHubDFactory.create(
            hub_in=hub_b_expired,
            hub_out=self.satd1.hub_entity,
            state_date_end=montrek_time(2020, 1, 1),
        )
        repo = self._hub_b_repo()
        qs = repo.filter_by_linked_hub(
            repo.receive(), me_models.LinkHubBHubD, self.satd1.hub_entity
        )
        hub_ids = list(qs.values_list("hub_id", flat=True))
        self.assertNotIn(hub_b_expired.id, hub_ids)

    # ------------------------------------------------------------------
    # Reversed direction: filter HubD rows by HubB (hub_in)
    # ------------------------------------------------------------------

    def test_reversed_link__returns_only_linked_row(self):
        """Only the HubD linked to hub_b1 should be returned."""
        repo = HubDRepository()
        qs = repo.filter_by_linked_hub(
            repo.receive(),
            me_models.LinkHubBHubD,
            self.satb1.hub_entity,
            reversed_link=True,
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].hub, self.satd1.hub_entity)

    def test_reversed_link__excludes_row_linked_to_different_target(self):
        """HubD linked to hub_b2 must not appear when filtering by hub_b1."""
        repo = HubDRepository()
        qs = repo.filter_by_linked_hub(
            repo.receive(),
            me_models.LinkHubBHubD,
            self.satb1.hub_entity,
            reversed_link=True,
        )
        hub_ids = list(qs.values_list("hub_id", flat=True))
        self.assertNotIn(self.satd2.hub_entity_id, hub_ids)


class TestTSSatelliteLinkSatelliteFilterCount(TestCase):
    """
    Regression: link_satellite_filter on a TS satellite with agg_func="count" must
    return 0 when all satellites fail the filter — not the total unfiltered count.

    Root cause: SQL COUNT() returns 0 (not NULL) for empty sets, so the outer COUNT
    in _link_hubs_and_get_ts_subquery was treating those zeros as valid (non-NULL)
    entries and counting them.  The fix applies NullIf(inner_subquery, 0) to convert
    zero inner counts to NULL so the outer COUNT skips them.

    Setup: DHubValueDate (outer) ← LinkHubCHubD (M2M) ← HubC ← CHubValueDate ← SatTSC2
    """

    def setUp(self):
        self.reference_date = montrek_time(2023, 6, 25)
        shared_vdl = ValueDateListFactory()

        hub_d = me_factories.HubDFactory()
        self.outer_hvd = me_factories.DHubValueDateFactory(
            hub=hub_d, value_date_list=shared_vdl
        )

        hub_c_1 = me_factories.HubCFactory()
        inner_hvd_1 = me_factories.CHubValueDateFactory(
            hub=hub_c_1, value_date_list=shared_vdl
        )
        me_factories.LinkHubCHubDFactory(hub_in=hub_c_1, hub_out=hub_d)
        self.sat_1 = me_factories.SatTSC2Factory(
            hub_value_date=inner_hvd_1, field_tsc2_float=0.0
        )

        hub_c_2 = me_factories.HubCFactory()
        inner_hvd_2 = me_factories.CHubValueDateFactory(
            hub=hub_c_2, value_date_list=shared_vdl
        )
        me_factories.LinkHubCHubDFactory(hub_in=hub_c_2, hub_out=hub_d)
        self.sat_2 = me_factories.SatTSC2Factory(
            hub_value_date=inner_hvd_2, field_tsc2_float=0.0
        )

    def _annotate(self, link_satellite_filter=None):
        builder = ReverseLinkedSatelliteSubqueryBuilder(
            satellite_class=me_models.SatTSC2,
            field="hub_value_date_id",
            link_class=me_models.LinkHubCHubD,
            agg_func="count",
            link_satellite_filter=link_satellite_filter,
        )
        return me_models.DHubValueDate.objects.annotate(
            linked_count=builder.build(self.reference_date)
        ).get(pk=self.outer_hvd.pk)

    def test_count_without_filter_returns_total(self):
        self.assertEqual(self._annotate().linked_count, 2)

    def test_count_with_filter_matching_none_returns_zero(self):
        # field_tsc2_float=0.0 for both → __gt=0 excludes everything → must be 0, not 2.
        # Before the fix this returned 2 because COUNT(0, 0) = 2.
        result = self._annotate(link_satellite_filter={"field_tsc2_float__gt": 0})
        self.assertEqual(result.linked_count, 0)

    def test_count_with_filter_matching_one_returns_one(self):
        self.sat_1.field_tsc2_float = 1.0
        self.sat_1.save()
        result = self._annotate(link_satellite_filter={"field_tsc2_float__gt": 0})
        self.assertEqual(result.linked_count, 1)

    def test_count_with_filter_matching_all_returns_total(self):
        self.sat_1.field_tsc2_float = 1.0
        self.sat_1.save()
        self.sat_2.field_tsc2_float = 1.0
        self.sat_2.save()
        result = self._annotate(link_satellite_filter={"field_tsc2_float__gt": 0})
        self.assertEqual(result.linked_count, 2)

    def test_count_with_negated_q_filter(self):
        # Q objects are accepted alongside plain dicts and support negation;
        # covers the TS satellite path (_annotate_ts_satellite_dict).
        self.sat_1.field_tsc2_float = 1.0
        self.sat_1.save()
        result = self._annotate(link_satellite_filter=~Q(field_tsc2_float=0.0))
        self.assertEqual(result.linked_count, 1)


class TestHubSatelliteFilter(TestCase):
    """Tests for hub_satellite_filter on add_satellite_fields_annotations.

    hub_satellite_filter switches the TS satellite lookup from per-HVD to
    hub-level, returning the latest satellite matching the filter criteria
    across the hub's full history.  Requires latest_ts=True on the repository.
    """

    def setUp(self):
        # hub_c_1: three time-series entries at ascending dates
        sat_jan = me_factories.SatTSC2Factory.create(
            value_date="2026-01-01", field_tsc2_float=1.0
        )
        self.hub_c_1 = sat_jan.hub_value_date.hub
        hvd_feb = me_factories.CHubValueDateFactory.create(
            hub=self.hub_c_1,
            value_date_list=ValueDateListFactory.create(value_date="2026-02-01"),
        )
        me_factories.SatTSC2Factory.create(hub_value_date=hvd_feb, field_tsc2_float=2.0)
        hvd_mar = me_factories.CHubValueDateFactory.create(
            hub=self.hub_c_1,
            value_date_list=ValueDateListFactory.create(value_date="2026-03-01"),
        )
        me_factories.SatTSC2Factory.create(hub_value_date=hvd_mar, field_tsc2_float=3.0)

        # hub_c_2: single entry — no previous value exists
        sat_only = me_factories.SatTSC2Factory.create(
            value_date="2026-01-01", field_tsc2_float=5.0
        )
        self.hub_c_2 = sat_only.hub_value_date.hub

    # --- previous-value filter ---

    def test_prev_value_is_the_immediately_preceding_entry(self):
        repo = HubCRepositoryLastTS()
        qs = repo.receive().get(hub_entity_id=self.hub_c_1.pk)
        self.assertEqual(qs.field_tsc2_float, 3.0)
        self.assertEqual(qs.prev_field_tsc2_float, 2.0)

    def test_prev_value_is_none_when_only_one_entry_exists(self):
        repo = HubCRepositoryLastTS()
        qs = repo.receive().get(hub_entity_id=self.hub_c_2.pk)
        self.assertEqual(qs.field_tsc2_float, 5.0)
        self.assertIsNone(qs.prev_field_tsc2_float)

    def test_prev_value_is_not_the_oldest_but_the_second_latest(self):
        # Verifies that ORDER BY date DESC LIMIT 1 picks the entry just before
        # the latest, not the oldest one in the history.
        repo = HubCRepositoryLastTS()
        qs = repo.receive().get(hub_entity_id=self.hub_c_1.pk)
        self.assertNotEqual(qs.prev_field_tsc2_float, 1.0)
        self.assertEqual(qs.prev_field_tsc2_float, 2.0)

    # --- property filter ---

    def test_property_filter_returns_latest_satellite_matching_condition(self):
        # hub_c_1 has values [1.0, 2.0, 3.0]; filter __gte=2.0 → latest match is 3.0
        repo = HubCRepositoryPropertyFilter()
        qs = repo.receive().get(hub_entity_id=self.hub_c_1.pk)
        self.assertEqual(qs.field_tsc2_float, 3.0)

    def test_property_filter_skips_non_matching_satellites(self):
        # hub_c_2 has only value 5.0 which satisfies __gte=2.0
        repo = HubCRepositoryPropertyFilter()
        qs = repo.receive().get(hub_entity_id=self.hub_c_2.pk)
        self.assertEqual(qs.field_tsc2_float, 5.0)

    def test_property_filter_returns_none_when_no_satellite_matches(self):
        sat = me_factories.SatTSC2Factory.create(
            value_date="2026-01-01", field_tsc2_float=0.5
        )
        hub_no_match = sat.hub_value_date.hub
        repo = HubCRepositoryPropertyFilter()
        qs = repo.receive().get(hub_entity_id=hub_no_match.pk)
        self.assertIsNone(qs.field_tsc2_float)

    # --- warning ---

    def test_warning_emitted_when_hub_satellite_filter_used_with_latest_ts_false(self):
        class _MisconfiguredRepo(MontrekRepository):
            hub_class = me_models.HubC
            latest_ts = False

            def set_annotations(self):
                self.add_satellite_fields_annotations(
                    me_models.SatTSC2,
                    ["field_tsc2_float"],
                    hub_satellite_filter={"field_tsc2_float__gte": 2.0},
                )

        with self.assertWarns(UserWarning) as cm:
            _MisconfiguredRepo({})
        self.assertIn("hub_satellite_filter", str(cm.warning))


class TestQuerysetForwardedToSubqueryBuilder(TestCase):
    """
    Regression test for forwarding the intermediate queryset to SubqueryBuilder.build().

    ``_QuerysetAwareSubqueryBuilder`` performs a Python-side computation that
    requires the intermediate queryset (carrying ``field_projections``
    annotations). Without forwarding it returns ``None`` for every row.
    """

    def setUp(self):
        me_factories.SatA1Factory(field_a1_int=5)
        me_factories.SatA1Factory(field_a1_int=10)

    def test_queryset_forwarded_to_subquery_builder(self):
        qs = HubAQuerysetAwareRepository().receive().order_by("field_a1_int")
        self.assertEqual(qs[0].field_a1_int_doubled, 10)
        self.assertEqual(qs[1].field_a1_int_doubled, 20)


class TestScalarLinkedTSSatelliteAlias(TestCase):
    """Tests for the TS alias optimization path (_build_ts_scalar_alias).

    When annotating multiple fields from a scalar linked timeseries satellite
    (one satellite row per hub row), the Annotator shares a single alias
    subquery that resolves the satellite pk at the matching value_date_list,
    and each field is then resolved via a cheap pk-lookup projection.

    The four cases cover:
    - correct field values when value_dates match
    - isolation: only the satellite at the matching value_date is used
    - expired satellite (state_date_end before reference_date) → null
    - no link → null
    """

    def test_correct_fields_returned_for_matching_value_date(self):
        """Both projected fields from the linked TS satellite are returned
        correctly, confirming that the shared alias resolves the right pk."""
        sat_tsc3 = me_factories.SatTSC3Factory(
            value_date="2024-01-15", field_tsc3_int=42, field_tsc3_str="hello"
        )
        hvd_a = me_factories.AHubValueDateFactory(value_date="2024-01-15")
        me_factories.LinkHubAHubCFactory(
            hub_in=hvd_a.hub, hub_out=sat_tsc3.hub_value_date.hub
        )

        qs = HubATSLinkedRepository().receive()
        self.assertEqual(qs.count(), 1)
        obj = qs.get()
        self.assertEqual(obj.field_tsc3_int, 42)
        self.assertEqual(obj.field_tsc3_str, "hello")

    def test_value_date_isolation(self):
        """A HubA row at value_date A retrieves the satellite for date A only —
        not the satellite at date B — even when both HubA rows are linked to the
        same HubC that has satellites at both dates."""
        hub_c = me_factories.HubCFactory()

        # January CHubValueDate + SatTSC3
        hvd_c_jan = me_factories.CHubValueDateFactory.create(
            hub=hub_c,
            value_date_list=ValueDateListFactory.create(value_date="2024-01-15"),
        )
        me_factories.SatTSC3Factory.create(hub_value_date=hvd_c_jan, field_tsc3_int=10)

        # February CHubValueDate + SatTSC3
        hvd_c_feb = me_factories.CHubValueDateFactory.create(
            hub=hub_c,
            value_date_list=ValueDateListFactory.create(value_date="2024-02-01"),
        )
        me_factories.SatTSC3Factory.create(hub_value_date=hvd_c_feb, field_tsc3_int=20)

        # HubA linked for January value date
        hvd_a_jan = me_factories.AHubValueDateFactory.create(value_date="2024-01-15")
        me_factories.LinkHubAHubCFactory(hub_in=hvd_a_jan.hub, hub_out=hub_c)

        # HubA linked for February value date
        hvd_a_feb = me_factories.AHubValueDateFactory.create(value_date="2024-02-01")
        me_factories.LinkHubAHubCFactory(hub_in=hvd_a_feb.hub, hub_out=hub_c)

        qs = HubATSLinkedRepository().receive().order_by("value_date")
        self.assertEqual(qs.count(), 2)
        self.assertEqual(qs[0].field_tsc3_int, 10)  # Jan row → Jan satellite
        self.assertEqual(qs[1].field_tsc3_int, 20)  # Feb row → Feb satellite

    def test_expired_satellite_returns_null(self):
        """A satellite whose state_date_end is before the reference_date is not
        matched by the alias subquery (state validity filter fails), so both
        projected fields are null."""
        ref_date = montrek_time(2024, 6, 1)
        sat_tsc3 = me_factories.SatTSC3Factory(
            value_date="2024-01-15",
            field_tsc3_int=42,
            field_tsc3_str="hello",
            state_date_end=montrek_time(2024, 5, 1),  # expires before ref_date
        )
        hvd_a = me_factories.AHubValueDateFactory(value_date="2024-01-15")
        me_factories.LinkHubAHubCFactory(
            hub_in=hvd_a.hub, hub_out=sat_tsc3.hub_value_date.hub
        )

        repo = HubATSLinkedRepository({"reference_date": ref_date})
        obj = repo.receive().get()
        self.assertIsNone(obj.field_tsc3_int)
        self.assertIsNone(obj.field_tsc3_str)

    def test_no_link_returns_null(self):
        """A HubA row with no link to any HubC yields null for all projected
        fields from the linked TS satellite."""
        me_factories.AHubValueDateFactory(value_date="2024-01-15")
        # No LinkHubAHubCFactory — intentionally unlinked

        qs = HubATSLinkedRepository().receive()
        self.assertEqual(qs.count(), 1)
        obj = qs.get()
        self.assertIsNone(obj.field_tsc3_int)
        self.assertIsNone(obj.field_tsc3_str)


class TestJsonAggLinks(TestCase):
    def setUp(self):
        self.hub_c = me_factories.HubCFactory()

    def test_json_agg__no_linked_value(self):
        obj = HubCRepositoryJsonAgg().receive().get()
        self.assertIsNone(obj.field_d1_str)

    def test_json_agg__single_value(self):
        sat_d = me_factories.SatD1Factory(field_d1_str="hello")
        self.hub_c.link_hub_c_hub_d.add(sat_d.hub_entity)
        obj = HubCRepositoryJsonAgg().receive().get()
        self.assertEqual(json.loads(obj.field_d1_str), ["hello"])

    def test_json_agg__multiple_values(self):
        sat_d1 = me_factories.SatD1Factory(field_d1_str="first")
        sat_d2 = me_factories.SatD1Factory(field_d1_str="second")
        self.hub_c.link_hub_c_hub_d.add(sat_d1.hub_entity)
        self.hub_c.link_hub_c_hub_d.add(sat_d2.hub_entity)
        obj = HubCRepositoryJsonAgg().receive().get()
        self.assertCountEqual(json.loads(obj.field_d1_str), ["first", "second"])

    def test_json_agg__value_containing_separator(self):
        sat_d = me_factories.SatD1Factory(field_d1_str="prompt; important")
        self.hub_c.link_hub_c_hub_d.add(sat_d.hub_entity)
        obj = HubCRepositoryJsonAgg().receive().get()
        self.assertEqual(json.loads(obj.field_d1_str), ["prompt; important"])

    def test_json_agg__value_containing_comma(self):
        sat_d = me_factories.SatD1Factory(field_d1_str="A, B")
        self.hub_c.link_hub_c_hub_d.add(sat_d.hub_entity)
        obj = HubCRepositoryJsonAgg().receive().get()
        self.assertEqual(json.loads(obj.field_d1_str), ["A, B"])

    def test_json_agg__hub_d_ids_aggregated(self):
        sat_d1 = me_factories.SatD1Factory(field_d1_str="x")
        sat_d2 = me_factories.SatD1Factory(field_d1_str="y")
        self.hub_c.link_hub_c_hub_d.add(sat_d1.hub_entity)
        self.hub_c.link_hub_c_hub_d.add(sat_d2.hub_entity)
        obj = HubCRepositoryJsonAgg().receive().get()
        hub_d_ids = json.loads(obj.hub_d_id)
        self.assertCountEqual(
            hub_d_ids,
            [sat_d1.hub_entity_id, sat_d2.hub_entity_id],
        )


class TestGetLinkNames(TestCase):
    def _assert_get_links(
        self, repo: type[MontrekRepository], expected_links: list[str]
    ):
        links = repo().get_link_names()
        self.assertEqual(links, expected_links)

    def test_get_repository_link_names(self):
        for repo, expected_links in [
            (
                HubARepository,
                [
                    "link_hub_a_hub_b",
                    "link_hub_a_hub_c",
                    "link_hub_a_file_upload_registry",
                    "link_hub_a_api_upload_registry",
                ],
            ),
            (HubBRepository, ["link_hub_b_hub_d", "link_hub_b_hub_a"]),
            (HubCRepository, ["link_hub_c_hub_d", "link_hub_c_hub_a"]),
            (
                HubDRepository,
                ["link_hub_d_hub_e", "link_hub_d_hub_b", "link_hub_d_hub_c"],
            ),
        ]:
            with self.subTest(f"Assert links for {repo}"):
                self._assert_get_links(repo, expected_links)


class TestLinkSatelliteFilterQObjects(TestCase):
    """link_satellite_filter accepts Q objects in addition to plain filter
    dicts. Q objects allow negated conditions (~Q), which cannot be expressed
    as filter kwargs.
    """

    def test_negated_q_excludes_matching_linked_satellites(self):
        # Multi-link annotation path (_link_hubs_and_get_subquery).
        hub_c = me_factories.HubCFactory()
        for name in ("first", "second", "EXCLUDED"):
            sat_d = me_factories.SatD1Factory(field_d1_str=name)
            hub_c.link_hub_c_hub_d.add(sat_d.hub_entity)

        obj = HubCRepositoryLinkSatelliteQFilter().receive().get()
        self.assertCountEqual(json.loads(obj.field_d1_str), ["first", "second"])

    def test_negated_q_on_scalar_link_alias_path(self):
        # Scalar (one-to-one) links resolve the satellite through a shared
        # alias subquery (_build_scalar_alias) instead of the multi-link path.
        sat_b_keep = me_factories.SatB1Factory(field_b1_str="kept")
        sat_b_excluded = me_factories.SatB1Factory(field_b1_str="EXCLUDED")
        hub_a_keep = me_factories.HubAFactory(hub_b=sat_b_keep.hub_entity)
        hub_a_excluded = me_factories.HubAFactory(hub_b=sat_b_excluded.hub_entity)

        queryset = HubARepositoryLinkSatelliteQFilter().receive()
        self.assertEqual(queryset.get(hub_entity_id=hub_a_keep.pk).field_b1_str, "kept")
        self.assertIsNone(queryset.get(hub_entity_id=hub_a_excluded.pk).field_b1_str)


class TestLinkSatelliteFilterQOuterRef(TestCase):
    """A link_satellite_filter Q object can reference an annotation of the
    outer queryset via a double OuterRef (the satellite subquery is nested two
    levels below the main queryset).

    HubCRepositoryLinkSatelliteQOuterRefFilter excludes linked SatD1 rows whose
    field_d1_int equals the outer row's field_tsc3_int annotation, coalescing
    NULL to a sentinel so rows without an outer value keep all linked entries.
    """

    def _make_hub_c_with_linked_d_ints(self, field_tsc3_int):
        sat_tsc3 = me_factories.SatTSC3Factory(
            value_date="2024-01-15", field_tsc3_int=field_tsc3_int
        )
        hub_c = sat_tsc3.hub_value_date.hub
        for d_int in (7, 8):
            sat_d = me_factories.SatD1Factory(field_d1_int=d_int)
            hub_c.link_hub_c_hub_d.add(sat_d.hub_entity)
        return hub_c

    def test_linked_satellite_matching_outer_annotation_is_excluded(self):
        self._make_hub_c_with_linked_d_ints(field_tsc3_int=7)

        obj = HubCRepositoryLinkSatelliteQOuterRefFilter().receive().get()
        self.assertEqual(obj.field_tsc3_int, 7)
        self.assertEqual(json.loads(obj.field_d1_int), [8])

    def test_all_linked_satellites_kept_when_outer_annotation_is_null(self):
        # Without the Coalesce in the repository's filter, comparing against
        # NULL would evaluate to NULL and drop every linked row.
        self._make_hub_c_with_linked_d_ints(field_tsc3_int=None)

        obj = HubCRepositoryLinkSatelliteQOuterRefFilter().receive().get()
        self.assertIsNone(obj.field_tsc3_int)
        self.assertCountEqual(json.loads(obj.field_d1_int), [7, 8])

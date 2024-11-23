import datetime
import hashlib
import time

from django.test import TestCase
from django.utils import timezone

from baseclasses.models import (
    TestMontrekHub,
    TestMontrekSatellite,
    TestMontrekSatelliteNoIdFields,
)
from baseclasses.tests.factories.baseclass_factories import (
    TestMontrekHubFactory,
    TestMontrekSatelliteFactory,
)
from baseclasses.utils import montrek_time


class TestBaseClassModels(TestCase):
    def test_time_stamp_mixin(self):
        test_hub = TestMontrekHub(identifier="test_hub")
        test_hub.save()
        self.assertAlmostEqual(
            test_hub.created_at, timezone.now(), delta=datetime.timedelta(seconds=1)
        )
        self.assertIsNotNone(test_hub.created_at)
        self.assertIsNotNone(test_hub.updated_at)
        self.assertAlmostEqual(
            test_hub.created_at,
            test_hub.updated_at,
            delta=datetime.timedelta(seconds=1),
        )
        test_hub.identifier = "test_hub_upd"
        time.sleep(2)
        test_hub.save()
        self.assertAlmostEqual(
            test_hub.updated_at, timezone.now(), delta=datetime.timedelta(seconds=1)
        )
        self.assertNotAlmostEqual(
            test_hub.created_at,
            test_hub.updated_at,
            delta=datetime.timedelta(seconds=1),
        )


class TestModelUtils(TestCase):
    def setUp(self):
        self.hub1 = TestMontrekHubFactory()
        self.hub2 = TestMontrekHubFactory()
        self.hub3 = TestMontrekHubFactory()
        self.satellite1 = TestMontrekSatelliteFactory(
            hub_entity=self.hub1,
            state_date_end=montrek_time(2023, 7, 10),
            state_date_start=montrek_time(2023, 6, 20),
        )
        self.satellite2 = TestMontrekSatelliteFactory(
            hub_entity=self.hub2,
            state_date_end=montrek_time(2023, 7, 10),
            state_date_start=montrek_time(2023, 6, 20),
        )
        self.satellite3 = TestMontrekSatelliteFactory(
            hub_entity=self.hub3,
            state_date_end=montrek_time(2023, 7, 10),
            state_date_start=montrek_time(2023, 6, 20),
        )

    def test_state_date(self):
        test_satellites = TestMontrekSatellite.objects.all()
        for test_satellite in test_satellites:
            self.assertEqual(
                test_satellite.state_date_start,
                timezone.datetime(2023, 6, 20, tzinfo=datetime.timezone.utc),
            )
            self.assertEqual(
                test_satellite.state_date_end,
                timezone.datetime(2023, 7, 10, tzinfo=datetime.timezone.utc),
            )


class TestSatelliteIdentifier(TestCase):
    def test_satellite_has_no_identifier_fields(self):
        with self.assertRaises(AttributeError) as e:
            test_object = TestMontrekSatelliteNoIdFields()
            test_object.save()
        self.assertEqual(
            str(e.exception),
            "Satellite TestMontrekSatelliteNoIdFields must have property identifier_fields",
        )

    def test_new_satellite_has_correct_identifier_hash(self):
        test_hash = hashlib.sha256(b"test_name").hexdigest()
        test_satellite = TestMontrekSatelliteFactory(
            test_name="test_name", hub_entity=TestMontrekHubFactory()
        )
        self.assertEqual(test_satellite.hash_identifier, test_hash)

    def test_new_satellite_has_incorrect_identifier_hash(self):
        test_hash = hashlib.sha256(b"test_name").hexdigest()
        test_satellite = TestMontrekSatelliteFactory(
            test_name="test_name_2", hub_entity=TestMontrekHubFactory()
        )
        self.assertNotEqual(test_satellite.hash_identifier, test_hash)

    def test_satellite_hash_identifier_with_decimal(self):
        test_satellite = TestMontrekSatelliteFactory(
            test_name="test_name",
            test_decimal=1234.56,
            hub_entity=TestMontrekHubFactory.create(),
        )
        hash_unsaved = test_satellite.hash_identifier
        test_satellite.save()
        satellite_from_db = TestMontrekSatellite.objects.get(pk=test_satellite.pk)
        hash_saved = satellite_from_db.hash_identifier
        self.assertEqual(hash_unsaved, hash_saved)


class TestSatelliteValueHash(TestCase):
    def test_new_satellite_has_correct_value_hash(self):
        test_hash = hashlib.sha256(b"test_nameNone0").hexdigest()
        test_satellite = TestMontrekSatelliteFactory(
            test_name="test_name", hub_entity=TestMontrekHubFactory()
        )
        self.assertEqual(test_satellite.hash_value, test_hash)

    def test_new_satellite_has_wrong_value_hash(self):
        test_hash = hashlib.sha256(b"test_name").hexdigest()
        test_satellite = TestMontrekSatelliteFactory(
            test_name="test_name_2", hub_entity=TestMontrekHubFactory()
        )
        self.assertNotEqual(test_satellite.hash_value, test_hash)

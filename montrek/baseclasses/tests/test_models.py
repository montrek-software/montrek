import datetime
import time
import hashlib
from django.test import TestCase
from django.utils import timezone
from baseclasses.tests.factories.baseclass_factories import TestMontrekHubFactory, TestMontrekSatelliteFactory, TestMontrekLinkFactory
from baseclasses.models import TestMontrekSatellite
from baseclasses.models import TestMontrekHub
from baseclasses.models import TestMontrekSatellite
from baseclasses.models import TestMontrekLink
from baseclasses.models import TestMontrekSatelliteNoIdFields

class TestBaseClassModels(TestCase):
    def test_time_stamp_mixin(self):
        test_hub = TestMontrekHub(identifier='test_hub')
        test_hub.save()
        self.assertAlmostEqual(test_hub.created_at, timezone.now(),
                               delta=datetime.timedelta(seconds=1))
        self.assertIsNotNone(test_hub.created_at)
        self.assertIsNotNone(test_hub.updated_at)
        self.assertAlmostEqual(test_hub.created_at, test_hub.updated_at,
                               delta=datetime.timedelta(seconds=1))
        test_hub.identifier = 'test_hub_upd'
        time.sleep(2)
        test_hub.save()
        self.assertAlmostEqual(test_hub.updated_at, timezone.now(),
                               delta=datetime.timedelta(seconds=1))
        self.assertNotAlmostEqual(test_hub.created_at, test_hub.updated_at,
                                 delta=datetime.timedelta(seconds=1))


class TestModelUtils(TestCase):
    def setUp(self):
        self.hub1 = TestMontrekHubFactory()
        self.hub2 = TestMontrekHubFactory()
        self.hub3 = TestMontrekHubFactory()
        self.satellite1 = TestMontrekSatelliteFactory(hub_entity=self.hub1)
        self.satellite2 = TestMontrekSatelliteFactory(hub_entity=self.hub2)
        self.satellite3 = TestMontrekSatelliteFactory(hub_entity=self.hub3)
        self.link1 = TestMontrekLinkFactory(from_hub=self.hub1, to_hub=self.hub2)
        self.link2 = TestMontrekLinkFactory(from_hub=self.hub2, to_hub=self.hub3)
        self.link3 = TestMontrekLinkFactory(from_hub=self.hub3, to_hub=self.hub1)
        self.link4 = TestMontrekLinkFactory(from_hub=self.hub1, to_hub=self.hub3)
        self.link5 = TestMontrekLinkFactory(from_hub=self.hub3, to_hub=self.hub2)
        self.link6 = TestMontrekLinkFactory(from_hub=self.hub2, to_hub=self.hub1)

    def test_state_date(self):
        test_satellites = TestMontrekSatellite.objects.all()
        for test_satellite in test_satellites:
            self.assertEqual(
                test_satellite.state_date, timezone.datetime(2023,6,20, tzinfo=timezone.utc)
        )


class TestSatelliteIdentifier(TestCase):
    def test_satellite_has_no_identifier_fields(self):
        with self.assertRaises(AttributeError) as e:
            test_satellite = TestMontrekSatelliteNoIdFields.objects.create(
                hub_entity = TestMontrekHubFactory()
            )
        self.assertEqual(str(e.exception), 'Satellite TestMontrekSatelliteNoIdFields must have attribute identifier_fields')

    def test_new_satellite_has_correct_identifier_hash(self):
        test_hash = hashlib.sha256(b'test_name').hexdigest()
        test_satellite = TestMontrekSatelliteFactory(
            test_name='test_name',
            hub_entity=TestMontrekHubFactory()
        )
        self.assertEqual(test_satellite.hash_identifier, test_hash)

    def test_new_satellite_has_correct_identifier_hash(self):
        test_hash = hashlib.sha256(b'test_name').hexdigest()
        test_satellite = TestMontrekSatelliteFactory(
            test_name='test_name_2',
            hub_entity=TestMontrekHubFactory()
        )
        self.assertNotEqual(test_satellite.hash_identifier, test_hash)

class TestSatelliteValueHash(TestCase):
    def test_new_satellite_has_correct_value_hash(self):
        test_hash = hashlib.sha256(b'test_nameDEFAULT').hexdigest()
        test_satellite = TestMontrekSatelliteFactory(
            test_name='test_name',
            hub_entity=TestMontrekHubFactory()
        )
        self.assertEqual(test_satellite.hash_value, test_hash)

    def test_new_satellite_has_wrong_value_hash(self):
        test_hash = hashlib.sha256(b'test_name').hexdigest()
        test_satellite = TestMontrekSatelliteFactory(
            test_name='test_name_2',
            hub_entity=TestMontrekHubFactory()
        )
        self.assertNotEqual(test_satellite.hash_value, test_hash)

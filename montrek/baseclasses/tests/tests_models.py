import time
import datetime
from django.test import TestCase
from django.utils import timezone
from baseclasses.models import TestMontrekHub
from baseclasses.models import TestMontrekSatellite
from baseclasses.models import TestMontrekLink

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


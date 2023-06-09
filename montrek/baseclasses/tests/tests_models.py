from django.test import TestCase
from baseclass.models import TestMontrekHub
from baseclass.models import TestMontrekSatellite
from baseclass.models import TestMontrekLink

class TestBaseClassModels(TestCase):
    def test_time_stamp_mixin(self):
        test_hub = TestMontrekHub(identifier='test_hub')
        test_hub.save()
        self.assertIsNotNone(test_hub.created_at)
        self.assertIsNotNone(test_hub.updated_at)
        self.assertEqual(test_hub.created_at, test_hub.updated_at)
        test_hub.identifier = 'test_hub_updated'
        test_hub.save()
        self.assertNotEqual(test_hub.created_at, test_hub.updated_at)


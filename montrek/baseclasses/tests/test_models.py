from django.test import TestCase
from django.utils import timezone
from baseclasses.tests.factories.baseclass_factories import TestMontrekHubFactory, TestMontrekSatelliteFactory, TestMontrekLinkFactory
from baseclasses.models import TestMontrekSatellite

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

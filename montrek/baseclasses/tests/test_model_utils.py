from baseclasses.model_utils import get_hub_ids_by_satellite_attribute
from django.test import TestCase
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

    def test_get_hub_ids_by_satellite_attribute(self):
        self.assertEqual(
            get_hub_ids_by_satellite_attribute(TestMontrekSatellite,
                                               'test_name', 
                                               'Test Name 0'),
            [self.hub1.id])
        self.assertEqual(
            get_hub_ids_by_satellite_attribute(TestMontrekSatellite,
                                               'test_name',
                                               'Test Name 1'),
            [self.hub2.id])
        self.assertEqual(
            get_hub_ids_by_satellite_attribute(TestMontrekSatellite,
                                               'test_name',
                                               'Test Name 2'),
            [self.hub3.id])

    def test_get_hub_ids_by_satellite_attribute_raises_TypeError(self):
        with self.assertRaises(TypeError):
            get_hub_ids_by_satellite_attribute(TestMontrekSatellite,
                                               1,
                                               'Test Name 0')
        with self.assertRaises(TypeError):
            get_hub_ids_by_satellite_attribute(1,
                                               'test_name',
                                               'Test Name 0')


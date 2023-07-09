import pandas as pd
from freezegun import freeze_time
from django.test import TestCase
from django.utils import timezone

from baseclasses.repositories.db_helper import get_hub_ids_by_satellite_attribute
from baseclasses.repositories.db_helper import select_satellite
from baseclasses.repositories.db_helper import update_satellite
from baseclasses.repositories.db_helper import new_satellite_entry
from baseclasses.repositories.db_helper import new_satellites_bunch
from baseclasses.repositories.db_helper import new_satellites_bunch_from_df
from baseclasses.repositories.db_helper import new_satellites_bunch_from_df_and_from_hub_link
from baseclasses.tests.factories.baseclass_factories import TestMontrekHubFactory, TestMontrekSatelliteFactory, TestMontrekLinkFactory
from baseclasses.models import TestMontrekSatellite
from baseclasses.models import TestMontrekLink

class TestDBHelpers(TestCase):
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
                                               self.satellite1.test_name),
            [self.hub1.id])
        self.assertEqual(
            get_hub_ids_by_satellite_attribute(TestMontrekSatellite,
                                               'test_name',
                                               self.satellite2.test_name),
            [self.hub2.id])
        self.assertEqual(
            get_hub_ids_by_satellite_attribute(TestMontrekSatellite,
                                               'test_name',
                                               self.satellite3.test_name),
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

    def test_select_satellite_by_hub_id(self):
        test_hub = self.hub1
        selected_satellite = select_satellite(
            satellite_class=TestMontrekSatellite,
            hub_entity=test_hub)
        self.assertEqual(selected_satellite.state_date,
                timezone.datetime(2023,6,20, 0, 0, 0, tzinfo=timezone.utc)
                        )
        self.assertEqual(selected_satellite.hub_entity, test_hub)
        TestMontrekSatelliteFactory.create(hub_entity=self.hub1,
                                           state_date=timezone.datetime(2023,5,1))
        selected_satellite = select_satellite(
            hub_entity=test_hub,
            satellite_class=TestMontrekSatellite,
        )
        self.assertEqual(selected_satellite.state_date,
                timezone.datetime(2023,6,20, 0, 0, 0, tzinfo=timezone.utc)
                        )
        self.assertEqual(selected_satellite.hub_entity, test_hub)
        selected_satellite = select_satellite(
            satellite_class=TestMontrekSatellite,
            hub_entity=test_hub,
            reference_date=timezone.datetime(2023,5,20))
        self.assertEqual(selected_satellite.state_date,
                timezone.datetime(2023,5,1, 0, 0, 0, tzinfo=timezone.utc)
                        )
        self.assertEqual(selected_satellite.hub_entity, test_hub)
        test_hub_2 = self.hub2
        selected_satellite = select_satellite(
            satellite_class=TestMontrekSatellite,
            hub_entity=test_hub_2)
        self.assertEqual(selected_satellite.state_date,
                timezone.datetime(2023,6,20, 0, 0, 0, tzinfo=timezone.utc)
                        )
        self.assertEqual(selected_satellite.hub_entity, test_hub_2)

    def test_update_satellite_by_hub_id(self):
        test_satellite = self.satellite1
        test_satellite_name = test_satellite.test_name
        test_updated_satellite = update_satellite(
            satellite_instance=test_satellite,
            test_name='NewTestName')
        self.assertEqual(test_updated_satellite.test_name, 'NewTestName')
        self.assertEqual(test_updated_satellite.hub_entity, self.hub1)
        self.assertGreater(test_updated_satellite.state_date,
                           test_satellite.state_date) 
        test_updated_satellite_2 = update_satellite(
            satellite_instance=test_updated_satellite,
            state_date = timezone.datetime(2023,5,1, 0, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(test_updated_satellite_2.test_name, 'NewTestName')
        self.assertEqual(test_updated_satellite_2.hub_entity, self.hub1)
        self.assertEqual(test_updated_satellite_2.state_date,
                            timezone.datetime(2023,5,1, 0, 0, 0, tzinfo=timezone.utc))  

    def test_new_satellites_entry(self):
        test_satellite = new_satellite_entry(
            satellite_class=TestMontrekSatellite,
            hub_entity=self.hub1,
            test_name='NewTestName')
        self.assertEqual(test_satellite.test_name, 'NewTestName')
        self.assertEqual(test_satellite.hub_entity, self.hub1)
        self.assertEqual(test_satellite.state_date,
                            timezone.datetime(1,1,1, 0, 0, 0))

    def test_new_satellites_entry_no_hub(self):
        test_satellite = new_satellite_entry(
            satellite_class=TestMontrekSatellite,
            test_name='NewTestName')
        self.assertEqual(test_satellite.test_name, 'NewTestName')
        self.assertEqual(test_satellite.state_date,
                            timezone.datetime(1,1,1, 0, 0, 0))

    def test_new_satellites_bunch(self):
        test_satellites = new_satellites_bunch(
            satellite_class=TestMontrekSatellite,
            attributes = [{'test_name':'NewTestName'},
                          {'test_name':'NewTestName2'}])
        self.assertEqual(len(test_satellites), 2)
        self.assertEqual(test_satellites[0].test_name, 'NewTestName')
        self.assertEqual(test_satellites[0].state_date,
                            timezone.datetime(1,1,1, 0, 0, 0))
        self.assertEqual(test_satellites[1].test_name, 'NewTestName2')
        self.assertEqual(test_satellites[1].state_date,
                            timezone.datetime(1,1,1, 0, 0, 0))


    def test_new_satellites_bunch_from_df(self):
        test_df = pd.DataFrame({'test_name':['NewTestName','NewTestName2']})
        test_satellites = new_satellites_bunch_from_df(
            satellite_class=TestMontrekSatellite,
            import_df = test_df)
        self.assertEqual(len(test_satellites), 2)
        self.assertEqual(test_satellites[0].test_name, 'NewTestName')
        self.assertEqual(test_satellites[0].state_date,
                            timezone.datetime(1,1,1, 0, 0, 0))
        self.assertEqual(test_satellites[1].test_name, 'NewTestName2')
        self.assertEqual(test_satellites[1].state_date,
                            timezone.datetime(1,1,1, 0, 0, 0))

    def test_new_satellites_bunch_from_df_and_from_hub_link(self):
        test_df = pd.DataFrame({'test_name':['NewTestName','NewTestName2']})
        test_satellites = new_satellites_bunch_from_df_and_from_hub_link(
            satellite_class=TestMontrekSatellite,
            import_df = test_df,
            from_hub=self.hub1,
            link_table_class = TestMontrekLink
        )
        self.assertEqual(len(test_satellites), 2)
        self.assertEqual(test_satellites[0].test_name, 'NewTestName')
        self.assertEqual(test_satellites[0].state_date,
                            timezone.datetime(1,1,1, 0, 0, 0))
        self.assertEqual(test_satellites[1].test_name, 'NewTestName2')
        self.assertEqual(test_satellites[1].state_date,
                            timezone.datetime(1,1,1, 0, 0, 0))
        created_links = TestMontrekLink.objects.filter(
            to_hub__in=[sat.hub_entity for sat in test_satellites])
        self.assertTrue(created_links.exists())
        self.assertEqual(created_links.count(), len(test_satellites))
        self.assertTrue(all([link.from_hub == self.hub1 for link in created_links]))

    def test_new_satellite_exists_already(self):
       sat_values = {'test_name':'NewTestName',
                     'test_value': 'TestValue'} 
       test_hub = TestMontrekHubFactory()
       existing_sat = TestMontrekSatellite.objects.create(
           hub_entity=test_hub,
           **sat_values)
       new_sat = new_satellite_entry(satellite_class=TestMontrekSatellite,
                                     **sat_values)
       self.assertEqual(new_sat, existing_sat)
        

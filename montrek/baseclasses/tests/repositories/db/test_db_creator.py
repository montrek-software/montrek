import datetime

from django.test import TestCase

from baseclasses.models import (
    LinkTestMontrekTestLink,
    TestMontrekSatellite,
    TestMontrekTimeSeriesSatellite,
)
from baseclasses.repositories.db.db_creator import DbCreator
from baseclasses.tests.factories.baseclass_factories import (
    TestLinkHubFactory,
    TestMontrekSatelliteFactory,
    TestMontrekTimeSeriesSatelliteFactory,
    TestMontrekHubFactory,
)


class MockDbStaller:
    creation_date = datetime.datetime(2018, 1, 1, 0, 0, 0)


class TestDBCreator(TestCase):
    def test_make_timezone_aware(self):
        test_db_creator = DbCreator(MockDbStaller(), 1)
        test_datetime = datetime.datetime(2018, 1, 1, 0, 0, 0)
        test_db_creator._make_timezone_aware(test_datetime, "UTC")
        self.assertEqual(test_db_creator.data["UTC"].tzinfo.key, "UTC")

    def test_set_static_satellite_hub(self):
        test_db_creator = DbCreator(MockDbStaller(), 1)
        test_ts_sat = TestMontrekTimeSeriesSatelliteFactory.create()
        test_sat = TestMontrekSatelliteFactory.create()
        test_db_creator.new_satellites = {
            TestMontrekSatellite: test_sat,
            TestMontrekTimeSeriesSatellite: test_ts_sat,
        }
        test_db_creator.hub = test_ts_sat.hub_value_date.hub
        test_db_creator._set_static_satellites_hub()
        self.assertEqual(test_sat.hub_entity, test_ts_sat.hub_value_date.hub)

    def test_create_new_links(self):
        test_db_creator = DbCreator(MockDbStaller(), 1)
        test_hub = TestMontrekHubFactory()
        test_db_creator.hub = TestLinkHubFactory()
        result = test_db_creator._create_new_links(LinkTestMontrekTestLink, [test_hub])
        self.assertEqual(result[0].hub_out, test_db_creator.hub)
        self.assertEqual(result[0].hub_in, test_hub)

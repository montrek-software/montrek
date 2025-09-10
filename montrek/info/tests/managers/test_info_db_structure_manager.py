import pandas as pd
from django.test import TestCase
from info.managers.info_db_structure_manager import (
    DbStructureContainer,
    InfoDbStructureManager,
)


class TestInfoDbStructureManager(TestCase):
    def setUp(self):
        self.manager = InfoDbStructureManager()
        self.db_structure_container = self.manager.get_db_structure_container()
        self.example_app = "info"
        self.info_db_structure_container = self.db_structure_container[self.example_app]

    def test_db_structure_container_instance(self):
        self.assertIsInstance(self.info_db_structure_container, DbStructureContainer)

    def test_hub_counts(self):
        self.assertEqual(len(self.info_db_structure_container.hubs), 2)

    def test_hub_value_date_counts(self):
        self.assertEqual(len(self.info_db_structure_container.hub_value_dates), 2)

    def test_satellite_counts(self):
        self.assertEqual(len(self.info_db_structure_container.sats), 4)

    def test_time_series_satellite_counts(self):
        self.assertEqual(len(self.info_db_structure_container.ts_sats), 2)

    def test_link_counts(self):
        self.assertEqual(len(self.info_db_structure_container.links), 1)

    def test_hub_value_date_a(self):
        hub_value_date_a = self.info_db_structure_container.find_hub_value_date(
            "TestHubValueDateA"
        )
        self.assertEqual(hub_value_date_a.hub, "TestHubA")

    def test_hub_value_date_b(self):
        hub_value_date_b = self.info_db_structure_container.find_hub_value_date(
            "TestHubValueDateB"
        )
        self.assertEqual(hub_value_date_b.hub, "TestHubB")

    def test_time_series_satellite_hub_value_date(self):
        for ts_sat in self.info_db_structure_container.ts_sats:
            self.assertEqual(ts_sat.hub_value_date, "TestHubValueDateB")

    def test_satellite_hubs(self):
        expected_sat_hubs = (
            ("TestSatA1", "TestHubA"),
            ("TestSatA2", "TestHubA"),
            ("TestSatB1", "TestHubB"),
            ("TestSatB2", "TestHubB"),
        )
        for sat, hub in expected_sat_hubs:
            self.assertEqual(self.info_db_structure_container.find_sat(sat).hub, hub)

    def test_get_db_structure_df(self):
        test_df = self.manager.get_db_structure_df(self.db_structure_container)
        test_df = test_df.loc[test_df["app"] == self.example_app]
        self._assert_test_df(test_df)

    def test_get_db_structure_df__included_apps(self):
        manager = InfoDbStructureManager([self.example_app])
        test_df = manager.get_db_structure_df(manager.get_db_structure_container())
        self._assert_test_df(test_df)

    def _assert_test_df(self, test_df: pd.DataFrame):
        expected_data = [
            {
                "app": "info",
                "type": "Hub",
                "name": "TestHubB",
                "db_table_name": "info_testhubb",
                "link": "",
            },
            {
                "app": "info",
                "type": "Hub",
                "name": "TestHubA",
                "db_table_name": "info_testhuba",
                "link": "",
            },
            {
                "app": "info",
                "type": "HubValueDate",
                "name": "TestHubValueDateA",
                "db_table_name": "info_testhubvaluedatea",
                "link": "Hub: TestHubA",
            },
            {
                "app": "info",
                "type": "HubValueDate",
                "name": "TestHubValueDateB",
                "db_table_name": "info_testhubvaluedateb",
                "link": "Hub: TestHubB",
            },
            {
                "app": "info",
                "type": "Satellite",
                "name": "TestSatA1",
                "db_table_name": "info_testsata1",
                "link": "Hub: TestHubA",
            },
            {
                "app": "info",
                "type": "Satellite",
                "name": "TestSatA2",
                "db_table_name": "info_testsata2",
                "link": "Hub: TestHubA",
            },
            {
                "app": "info",
                "type": "Satellite",
                "name": "TestSatB1",
                "db_table_name": "info_testsatb1",
                "link": "Hub: TestHubB",
            },
            {
                "app": "info",
                "type": "Satellite",
                "name": "TestSatB2",
                "db_table_name": "info_testsatb2",
                "link": "Hub: TestHubB",
            },
            {
                "app": "info",
                "type": "TS Satellite",
                "name": "TestSatTSB1",
                "db_table_name": "info_testsattsb1",
                "link": "Hub Value Date: TestHubValueDateB",
            },
            {
                "app": "info",
                "type": "TS Satellite",
                "name": "TestSatTSB2",
                "db_table_name": "info_testsattsb2",
                "link": "Hub Value Date: TestHubValueDateB",
            },
            {
                "app": "info",
                "type": "Link",
                "name": "LinkTestHubATestHubB",
                "db_table_name": "info_linktesthubatesthubb",
                "link": "Hub in: TestHubA, Hub out: TestHubB",
            },
        ]
        test_df = test_df.reset_index(drop=True)

        pd.testing.assert_frame_equal(
            test_df, pd.DataFrame(expected_data), check_index_type=False
        )

    def test_get_db_structure_description(self):
        description = self.manager.get_db_structure_description(
            self.db_structure_container
        )
        expected_description = """info_testhubb:   Hub table in app info"""
        self.assertIn(
            expected_description.replace(" ", "").replace("\n", "").replace("\t", ""),
            description.replace(" ", "").replace("\n", "").replace("\t", ""),
        )

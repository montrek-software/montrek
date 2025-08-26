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

    def test_link_hubs(self):
        link = self.info_db_structure_container.find_link("LinkTestHubATestHubB")
        self.assertEqual(link.hub_in, "TestHubA")
        self.assertEqual(link.hub_out, "TestHubB")
        manager = InfoDbStructureManager()
        db_structure_container = manager.get_db_structure_container()
        example_app = "info"
        info_db_structure_container = db_structure_container[example_app]
        self.assertIsInstance(info_db_structure_container, DbStructureContainer)
        self.assertEqual(len(info_db_structure_container.hubs), 2)
        self.assertEqual(len(info_db_structure_container.hub_value_dates), 2)
        self.assertEqual(len(info_db_structure_container.sats), 4)
        self.assertEqual(len(info_db_structure_container.ts_sats), 2)
        self.assertEqual(len(info_db_structure_container.links), 1)
        hub_value_date_a = info_db_structure_container.find_hub_value_date(
            "TestHubValueDateA"
        )
        self.assertEqual(hub_value_date_a.hub, "TestHubA")
        hub_value_date_b = info_db_structure_container.find_hub_value_date(
            "TestHubValueDateB"
        )
        self.assertEqual(hub_value_date_b.hub, "TestHubB")
        for ts_sat in info_db_structure_container.ts_sats:
            self.assertEqual(ts_sat.hub_value_date, "TestHubValueDateB")
        expected_sat_hubs = (
            ("TestSatA1", "TestHubA"),
            ("TestSatA2", "TestHubA"),
            ("TestSatB1", "TestHubB"),
            ("TestSatB2", "TestHubB"),
        )
        for sat, hub in expected_sat_hubs:
            self.assertEqual(info_db_structure_container.find_sat(sat).hub, hub)
        link = info_db_structure_container.find_link("LinkTestHubATestHubB")
        self.assertEqual(link.hub_in, "TestHubA")
        self.assertEqual(link.hub_out, "TestHubB")

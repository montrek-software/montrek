from django.test import TestCase
from info.managers.info_db_structure_manager import (
    DbStructureContainer,
    InfoDbStructureManager,
)


class TestInfoDbStructureManager(TestCase):
    def test_get_db_structure_container(self):
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

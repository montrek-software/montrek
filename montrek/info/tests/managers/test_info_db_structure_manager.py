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
        self.assertIsInstance(db_structure_container[example_app], DbStructureContainer)
        self.assertEqual(len(db_structure_container[example_app].hubs), 2)
        self.assertEqual(len(db_structure_container[example_app].hub_value_dates), 2)
        self.assertEqual(len(db_structure_container[example_app].sats), 4)
        self.assertEqual(len(db_structure_container[example_app].ts_sats), 2)
        self.assertEqual(len(db_structure_container[example_app].links), 1)

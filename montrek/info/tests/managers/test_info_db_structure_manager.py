from django.test import TestCase
from django.test.utils import override_settings
from info.managers.info_db_structure_manager import (
    DbStructureContainer,
    InfoDbStructureManager,
)


@override_settings(INSTALLED_APPS=["info"])
class TestInfoDbStructureManager(TestCase):
    def test_get_db_structure_container(self):
        manager = InfoDbStructureManager()
        db_structure_container = manager.get_db_structure_container()
        example_app = "info"
        self.assertIsInstance(db_structure_container[example_app], DbStructureContainer)
        self.assertEqual(len(db_structure_container[example_app].hubs), 2)

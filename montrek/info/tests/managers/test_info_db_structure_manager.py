from django.test import TestCase
from info.managers.info_db_structure_manager import (
    DbStructureContainer,
    InfoDbStructureManager,
)


class TestInfoDbStructureManager(TestCase):
    def test_get_db_structure_container(self):
        manager = InfoDbStructureManager()
        db_structure_container = manager.get_db_structure_container()
        self.assertIsInstance(db_structure_container["info"], DbStructureContainer)

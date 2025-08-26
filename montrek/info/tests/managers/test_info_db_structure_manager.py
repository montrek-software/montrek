from django.test import TestCase
from info.managers.info_db_structure_manager import InfoDbStructureManager


class TestInfoDbStructureManager(TestCase):
    def test_get_model_container(self):
        manager = InfoDbStructureManager()

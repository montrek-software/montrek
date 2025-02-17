from django.test import TestCase

from file_upload.forms import FieldMapCreateForm
from file_upload.managers.field_map_manager import FieldMapManager
from file_upload.repositories.field_map_repository import FieldMapRepository


class TestFieldMapCreateForm(TestCase):
    def test_set_function_name_initial(self):
        form = FieldMapCreateForm(
            **{
                "initial": {"function_name": "test_function"},
                "field_map_manager": FieldMapManager({}),
                "repository": FieldMapRepository({}),
            }
        )
        self.assertEqual(form.initial["function_name"], "test_function")

    def test_function_name_initial_not_set(self):
        form = FieldMapCreateForm(
            **{
                "field_map_manager": FieldMapManager({}),
                "repository": FieldMapRepository({}),
            }
        )
        self.assertEqual(form.initial["function_name"], "no_change")

from file_upload.forms import FieldMapCreateForm
from django.test import TestCase


class TestFieldMapCreateForm(TestCase):
    def test_get_database_field_choices(self):
        choices = FieldMapCreateForm.get_database_field_choices()
        self.assertIn("field_a1_int", choices)
        self.assertIn("field_a2_str", choices)

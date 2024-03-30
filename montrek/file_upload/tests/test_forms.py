from file_upload.forms import FieldMapCreateForm
from django.test import TestCase

from file_upload.repositories.field_map_repository import FieldMapRepository


class TestFieldMapCreateForm(TestCase):
    def test_database_field_choices(self):
        form = FieldMapCreateForm(repository=FieldMapRepository())

        self.assertIn(
            ("field_a1_int", "field_a1_int"),
            form.fields["database_field"].choices,
        )
        self.assertIn(
            ("field_a2_str", "field_a2_str"),
            form.fields["database_field"].choices,
        )

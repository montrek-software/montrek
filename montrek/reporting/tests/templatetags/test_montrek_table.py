from django.test import TestCase
from reporting.templatetags.montrek_table import render_table
from reporting.tests.mocks import MockMontrekTableManager


class TestMontrekTableTemplatetag(TestCase):
    def test_simple_render_table(self):
        table_manager = MockMontrekTableManager({})
        rendered_template = render_table(table_manager)
        self.assertTrue("<h3>Mock Table</h3>" in rendered_template)

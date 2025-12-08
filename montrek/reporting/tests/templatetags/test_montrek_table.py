from django.test import TestCase
from reporting.templatetags.montrek_table import render_table
from reporting.tests.mocks import MockMontrekTableManager


class TestMontrekTableTemplatetag(TestCase):
    def test_simple_render_table(self):
        table_manager = MockMontrekTableManager({})
        rendered_template = render_table(table_manager)
        print(rendered_template)
        self.assertTrue("<h3>Mock Table</h3>" in rendered_template)

    def test_show_order_down(self):
        table_manager = MockMontrekTableManager({})
        table_manager.order_field = "field_a"
        rendered_template = render_table(table_manager)
        self.assertTrue(
            'FieldA</div><spanclass="bibi-arrow-down"></span>'
            in rendered_template.replace("\n", "").replace(" ", "")
        )

    def test_show_order_up(self):
        table_manager = MockMontrekTableManager({})
        table_manager.order_field = "field_a"
        table_manager.order_descending = True
        rendered_template = render_table(table_manager)
        self.assertTrue(
            'FieldA</div><spanclass="bibi-arrow-up"></span>'
            in rendered_template.replace("\n", "").replace(" ", "")
        )

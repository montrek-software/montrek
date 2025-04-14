from dataclasses import dataclass
from django.test import TestCase
from reporting.core.table_converter import LatexTableConverter
from reporting.dataclasses import table_elements as te


@dataclass
class MockQueryElement:
    test_col: str


class TestLatexTableConverter(TestCase):
    def setUp(self) -> None:
        self.table_elements = [te.StringTableElement(name="TestCol", attr="test_col")]
        self.table = [
            MockQueryElement(test_col="value1"),
            MockQueryElement(test_col="val2"),
        ]
        self.latex_table_converter = LatexTableConverter(
            "test_name", self.table_elements, self.table
        )

    def test_add_to_column_sizer(self):
        self.latex_table_converter.add_to_column_sizer(
            self.table_elements[0], self.table[0]
        )
        self.assertEqual(self.latex_table_converter.column_sizer["TestCol"], [6])
        self.latex_table_converter.add_to_column_sizer(
            self.table_elements[0], self.table[1]
        )
        self.assertEqual(self.latex_table_converter.column_sizer["TestCol"], [6, 4])
        test_col_sizes = self.latex_table_converter.get_column_sizes()
        expected_col_sizes = {"TestCol": 1.0}
        self.assertEqual(test_col_sizes, expected_col_sizes)

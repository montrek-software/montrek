from django.test import TestCase
from baseclasses.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from dataclasses import dataclass


@dataclass
class MockData:
    field_a: str
    field_b: int
    field_c: float


class MockRepository:
    def get_std_queryset(self):
        return [MockData("a", 1, 1.0), MockData("b", 2, 2.0), MockData("c", 3, 3.0)]


class MockMontrekTableManager(MontrekTableManager):
    repository_class = MockRepository

    @property
    def table_elements(
        self,
    ) -> tuple[te.StringTableElement, te.IntTableElement, te.FloatTableElement]:
        return (
            te.StringTableElement("field_a", "Field A"),
            te.IntTableElement("field_b", "Field B"),
            te.FloatTableElement("field_c", "Field C"),
        )


class TestMontrekTableManager(TestCase):
    def test_to_html(self):
        test_html = MockMontrekTableManager().to_html()
        self.assertEqual(test_html, "<table></table>")

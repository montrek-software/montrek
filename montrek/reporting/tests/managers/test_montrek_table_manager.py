from django.test import TestCase
from bs4 import BeautifulSoup
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from dataclasses import dataclass


@dataclass
class MockData:
    field_a: str
    field_b: int
    field_c: float


class MockRepository:
    def __init__(self, session_data: dict):
        self.session_data = session_data

    def std_queryset(self):
        return [MockData("a", 1, 1.0), MockData("b", 2, 2.0), MockData("c", 3, 3.0)]


class MockMontrekTableManager(MontrekTableManager):
    repository_class = MockRepository

    @property
    def table_elements(
        self,
    ) -> tuple[te.TableElement]:
        return (
            te.StringTableElement(attr="field_a", name="Field A"),
            te.IntTableElement(attr="field_b", name="Field B"),
            te.FloatTableElement(attr="field_c", name="Field C"),
            te.LinkTableElement(
                name="Link",
                url="home",
                kwargs={},
                hover_text="Link",
                icon="icon",
            ),
            te.LinkTextTableElement(
                name="Link Text",
                url="home",
                kwargs={},
                hover_text="Link Text",
                text="field_a",
            ),
        )


class TestMontrekTableManager(TestCase):
    def test_to_html(self):
        test_html = MockMontrekTableManager().to_html()
        soup = BeautifulSoup(test_html, "html.parser")
        table = soup.find("table")
        rows = table.find_all("tr")
        self.assertEqual(len(rows), 4)
        headers = soup.find_all("th")
        expected_headers = ["Field A", "Field B", "Field C", "Link", "Link Text"]
        header_texts = [th.get_text() for th in headers]
        self.assertEqual(header_texts, expected_headers)

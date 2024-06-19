import io
import pandas as pd
from django.test import TestCase
from django.http import HttpResponse
from bs4 import BeautifulSoup
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from dataclasses import dataclass


@dataclass
class MockData:
    field_a: str
    field_b: int
    field_c: float


class MockQuerySet:
    def __init__(self, *args):
        self.items = args

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]

    def __eq__(self, other):
        if isinstance(other, list):
            return list(self.items) == other
        return NotImplemented

    def all(self):
        return self.items


class MockRepository:
    def __init__(self, session_data: dict):
        self.session_data = session_data

    def std_queryset(self):
        return MockQuerySet(
            MockData("a", 1, 1.0), MockData("b", 2, 2.0), MockData("c", 3, 3.0)
        )


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


class MockHttpResponse:
    content: str = ""

    def write(self, content):
        self.content += content

    def getvalue(self):
        return self.content


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

    def test_to_latex(self):
        test_latex = MockMontrekTableManager().to_latex()
        self.assertTrue(test_latex.startswith("\n\\begin{table}"))
        self.assertTrue(test_latex.endswith("\\end{table}\n\n"))

    def test_download_csv(self):
        manager = MockMontrekTableManager()
        response = manager.download_csv(MockHttpResponse())
        self.assertEqual(
            response.getvalue(),
            "Field A,Field B,Field C,Link Text\r\na,1,1.0,a\r\nb,2,2.0,b\r\nc,3,3.0,c\r\n",
        )

    def test_download_excel(self):
        manager = MockMontrekTableManager()
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="export.xlsx"'
        response = manager.download_excel(response)
        self.assertEqual(response.status_code, 200)
        with io.BytesIO(response.content) as f:
            excel_file = pd.read_excel(f)
            expected_df = pd.DataFrame(
                {
                    "Field A": ["a", "b", "c"],
                    "Field B": [1, 2, 3],
                    "Field C": [1.0, 2.0, 3.0],
                    "Link Text": ["a", "b", "c"],
                }
            )
            pd.testing.assert_frame_equal(excel_file, expected_df, check_dtype=False)

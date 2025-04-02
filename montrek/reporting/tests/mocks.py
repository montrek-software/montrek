import datetime
from dataclasses import dataclass
from decimal import Decimal

import pandas as pd
from django.utils import timezone

from reporting.constants import ReportingPlotType
from reporting.core import reporting_text
from reporting.core.reporting_data import ReportingData
from reporting.core.reporting_grid_layout import ReportGridLayout
from reporting.core.reporting_plots import ReportingPlot
from reporting.dataclasses import table_elements as te
from reporting.managers.latex_report_manager import LatexReportManager
from reporting.managers.montrek_report_manager import (
    MontrekReportManager,
)
from reporting.managers.montrek_table_manager import (
    MontrekDataFrameTableManager,
    MontrekTableManager,
)


class MockNoCollectReportElements(MontrekReportManager):
    pass


class MockMontrekReportManager(MontrekReportManager):
    document_title = "Mock Report"

    def collect_report_elements(self):
        pass

    def generate_report(self) -> str:
        report = ""
        for report_element in self.report_elements:
            report += report_element.to_html()
            report += report_element.to_latex()
        return report


class MockReportElement:
    def to_html(self):
        return "html"

    def to_latex(self):
        return "latex"


class MockLatexReportManagerNoTemplate(LatexReportManager):
    latex_template = "no_template.tex"


class MockComprehensiveReportManager(MontrekReportManager):
    document_title = "Mock Comprehensive Report"

    def collect_report_elements(self):
        self.append_report_element(reporting_text.ReportingHeader1("Hallo"))
        self.append_report_element(self.grid())

    def grid(self):
        grid = ReportGridLayout(2, 2)
        grid.add_report_grid_element(reporting_text.ReportingParagraph("One"), 0, 0)
        grid.add_report_grid_element(reporting_text.ReportingParagraph("Two"), 0, 1)
        grid.add_report_grid_element(self.plot(grid.width), 1, 0)
        grid.add_report_grid_element(reporting_text.ReportingParagraph("Four"), 1, 1)
        return grid

    def plot(self, width):
        test_df = pd.DataFrame(
            {
                "Category": ["A", "B", "C", "D"],
                "Value": [10, 25, 15, 30],
            },
        )
        reporting_data = ReportingData(
            data_df=test_df,
            x_axis_column="Category",
            y_axis_columns=["Value"],
            plot_types=[ReportingPlotType.PIE],
            title="Test Plot",
        )
        reporting_plot = ReportingPlot(width=width)
        reporting_plot.generate(reporting_data)
        return reporting_plot


@dataclass
class MockData:
    field_a: str
    field_b: int
    field_c: float
    field_d: datetime.datetime | datetime.date | timezone.datetime
    field_e: Decimal


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

    def count(self) -> int:
        return len(self.items)


class MockRepository:
    def __init__(self, session_data: dict):
        self.session_data = session_data

    def receive(self):
        return MockQuerySet(
            MockData(
                "a",
                1,
                1.0,
                timezone.make_aware(datetime.datetime(2024, 7, 13)),
                Decimal(1),
            ),
            MockData("b", 2, 2.0, datetime.datetime(2024, 7, 13), Decimal(2.2)),
            MockData("c", 3, 3.0, timezone.datetime(2024, 7, 13), Decimal(3)),
        )

    def set_order_fields(self, value):
        self._order_field = value


class MockLongRepository:
    def __init__(self, session_data: dict):
        self.session_data = session_data
        self._order_field = None

    def receive(self):
        mock_data = [
            MockData(
                str(i), i, 1.0, timezone.make_aware(datetime.datetime(2024, 7, 13)), i
            )
            for i in range(10000)
        ]
        return MockQuerySet(*mock_data)

    def get_order_fields(self):
        return self._order_field

    def set_order_fields(self, value):
        self._order_field = value


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
            te.DateTimeTableElement(attr="field_d", name="Field D"),
            te.EuroTableElement(attr="field_e", name="Field E"),
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


class MockLongMontrekTableManager(MockMontrekTableManager):
    repository_class = MockLongRepository


class MockHttpResponse:
    content: str = ""

    def write(self, content):
        self.content += content

    def getvalue(self):
        return self.content


class MockMontrekDataFrameTableManager(MontrekDataFrameTableManager):
    repository_class = MockLongRepository

    @property
    def table_elements(
        self,
    ) -> tuple[te.TableElement]:
        return (
            te.StringTableElement(attr="field_a", name="Field A"),
            te.IntTableElement(attr="field_b", name="Field B"),
            te.FloatTableElement(attr="field_c", name="Field C"),
            te.DateTimeTableElement(attr="field_d", name="Field D"),
            te.EuroTableElement(attr="field_e", name="Field E"),
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

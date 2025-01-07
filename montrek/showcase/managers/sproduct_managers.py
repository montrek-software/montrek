from reporting.core.reporting_data import ReportingData
from django_pandas.io import read_frame
from reporting.core.reporting_plots import ReportingPlot
from reporting.managers.montrek_report_manager import MontrekReportManager
from reporting.managers.montrek_details_manager import MontrekDetailsManager
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.managers.stransaction_managers import (
    SProductTopTenSPositionsTableManager,
)
from showcase.repositories.sproduct_repositories import SProductRepository
from showcase.repositories.stransaction_repositories import SProductSPositionRepository


class SProductTableManager(MontrekTableManager):
    repository_class = SProductRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Product Name", attr="product_name"),
            te.LinkTableElement(
                name="Details",
                url="sproduct_details",
                kwargs={"pk": "id"},
                icon="eye-open",
                hover_text="View Product Details",
            ),
            te.LinkTableElement(
                name="Edit",
                url="sproduct_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Product",
            ),
            te.LinkTableElement(
                name="Delete",
                url="sproduct_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Product",
            ),
        ]


class SProductDetailsManager(MontrekDetailsManager):
    repository_class = SProductRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Product Name", attr="product_name"),
            te.DateTableElement(name="Inception Date", attr="inception_date"),
            te.LinkTableElement(
                name="Edit",
                url="sproduct_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Product",
            ),
            te.LinkTableElement(
                name="Delete",
                url="sproduct_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Product",
            ),
        ]


class SProductReportManager(MontrekReportManager):
    repository_class = SProductRepository
    position_repository_class = SProductSPositionRepository

    def __init__(self, session_data):
        super().__init__(session_data)
        self.obj = self.repository.receive().get(pk=session_data["pk"])
        self.positions_df = self._get_positions_df()

    def _get_positions_df(self):
        repository = self.position_repository_class(self.session_data)
        return read_frame(repository.receive())

    @property
    def document_title(self) -> str:
        return f"Holdings Report: {self.obj.product_name}"

    def collect_report_elements(self):
        self._add_top_ten_holdings_table()
        self._plot_allocation_pie("country_name", "Country Allocation")
        self._plot_allocation_pie("company_sector", "Sector Allocation")

    def _plot_allocation_pie(self, group_field, title):
        value_field = "value"
        allocation_df = self.positions_df.groupby(group_field)[[value_field]].sum()
        plot_data = ReportingData(
            allocation_df,
            title,
            x_axis_is_index=True,
            y_axis_columns=[value_field],
            plot_types=["pie"],
        )
        plot = ReportingPlot()
        plot.generate(plot_data)
        self.append_report_element(plot)

    def _add_top_ten_holdings_table(self):
        table_manager = SProductTopTenSPositionsTableManager(self.session_data)
        self.append_report_element(table_manager)

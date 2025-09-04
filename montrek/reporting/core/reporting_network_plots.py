from typing import Any

from plotly.graph_objs import Scatter
from reporting.core.reporting_data import ReportingNetworkData
from reporting.core.reporting_plots import ReportingPlotBase


class ReportingNetworkPlot(ReportingPlotBase[ReportingNetworkData]):
    def _check_reporting_data(self, reporting_data: ReportingNetworkData):
        return

    def _get_figure_data(
        self, _x: list[Any], reporting_data: ReportingNetworkData
    ) -> list[Scatter]:
        return []

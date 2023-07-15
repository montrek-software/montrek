from typing import Any, List
import plotly.graph_objects as go
from reporting.core.reporting_protocols import ReportingElement
from reporting.core.reporting_data import ReportingData
from reporting.core.reporting_mixins import ReportingChecksMixin
from reporting.constants import ReportingPlotType

class ReportingPlot(ReportingElement,
                    ReportingChecksMixin):

    def generate(self, reporting_data: ReportingData) -> None:
        self._check_reporting_data(reporting_data)
        _x = self._set_x_axis(reporting_data)

        figure_data = []
        for y_axis_column, plot_type in zip(reporting_data.y_axis_columns, reporting_data.plot_types):
            _y = reporting_data.data_df[y_axis_column]
            if plot_type == ReportingPlotType.BAR:
                figure_data.append(go.Bar(x=_x, y=_y))
            elif plot_type == ReportingPlotType.LINE:
                figure_data.append(go.Scatter(x=_x, y=_y))
            else:
                raise ValueError(f"Plot type {plot_type} not supported")
        self.figure = go.Figure(data=figure_data)

    def format_html(self) -> str:
        return self.figure.to_html(full_html=False, include_plotlyjs='cdn') 

    def _check_reporting_data(self, reporting_data: ReportingData) -> None:
        if len(reporting_data.y_axis_columns) != len(reporting_data.plot_types):
            raise ValueError("Number of y_axis_columns and plot_types must match")
        if not reporting_data.x_axis_is_index and reporting_data.x_axis_column is None:
            raise ValueError("x_axis_column must be provided if x_axis_is_index is False")

    def _set_x_axis(self, reporting_data: ReportingData) -> List[Any]:
        if reporting_data.x_axis_is_index:
            return reporting_data.data_df.index
        else:
            return reporting_data.data_df[reporting_data.x_axis_column]

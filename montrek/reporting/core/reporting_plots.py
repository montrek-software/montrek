import plotly.graph_objects as go
from reporting.core.reporting_protocols import ReportingElement
from reporting.core.reporting_data import ReportingData
from reporting.core.reporting_mixins import ReportingChecksMixin

class ReportingPlot(ReportingElement,
                    ReportingChecksMixin):

    def generate(self, data: ReportingData) -> None:
        if len(data.y_axis_columns) != len(data.plot_types):
            raise ValueError("Number of y_axis_columns and plot_types must match")

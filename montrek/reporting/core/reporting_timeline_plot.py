import plotly.express as px
import plotly.graph_objects as go
from reporting.core.reporting_data import ReportingTimelineData
from reporting.core.reporting_plots import ReportingPlotBase


class ReportingTimelinePlot(ReportingPlotBase[ReportingTimelineData]):
    def _check_reporting_data(self, reporting_data: ReportingTimelineData):
        return

    def get_figure(self, reporting_data: ReportingTimelineData) -> go.Figure:
        fig = px.timeline(
            reporting_data.timeline_df,
            x_start=reporting_data.start_date_col,
            x_end=reporting_data.end_date_col,
            y=reporting_data.item_name_col,
            color=reporting_data.item_name_col,
            # hover_data={
            #     "Start Date": "|%Y-%m-%d",
            #     "End Date": "|%Y-%m-%d",
            #     "Total Workdays": True,
            #     "Workdays Percentage": True,
            #     "Abnahme": True,
            #     "Signatur": True,
            #     "Name": False,  # already used as Y
            # },
        )
        return fig

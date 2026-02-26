from datetime import date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reporting.core.reporting_colors import ReportingColors
from reporting.core.reporting_data import ReportingTimelineData
from reporting.core.reporting_plots import ReportingPlotBase


class ReportingTimelinePlot(ReportingPlotBase[ReportingTimelineData]):
    def _check_reporting_data(self, reporting_data: ReportingTimelineData):
        # Validate that timeline_df is a pandas DataFrame
        if not isinstance(reporting_data.timeline_df, pd.DataFrame):
            raise ValueError("timeline_df must be a pandas DataFrame.")
        df = reporting_data.timeline_df
        # Validate required columns exist
        required_cols = [
            reporting_data.start_date_col,
            reporting_data.end_date_col,
            reporting_data.item_name_col,
        ]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in timeline_df.")
        # Validate item name column is string or categorical
        name_col = reporting_data.item_name_col
        if not (
            pd.api.types.is_string_dtype(df[name_col])
            or pd.api.types.is_categorical_dtype(df[name_col])
        ):
            raise ValueError(
                f"Column '{name_col}' must be of string or categorical type."
            )
        if reporting_data.report_date is not None and not isinstance(
            reporting_data.report_date, date
        ):
            raise TypeError(
                f"report_date must be a datetime.date object, "
                f"not {type(reporting_data.report_date).__name__}"
            )

    def get_figure(self, reporting_data: ReportingTimelineData) -> go.Figure:
        fig = px.timeline(
            reporting_data.timeline_df,
            x_start=reporting_data.start_date_col,
            x_end=reporting_data.end_date_col,
            y=reporting_data.item_name_col,
        )
        if reporting_data.report_date is not None:
            fig.add_vline(
                x=reporting_data.report_date,
                line_width=2,
                line_dash="dash",
                line_color="red",
            )
        return fig

    def update_axis_layout(self, reporting_data: ReportingTimelineData):
        self.figure.update_traces(
            marker_color=ReportingColors.BLUE.hex,
        )
        self.figure.update_layout(
            showlegend=False,
            yaxis_title=None,
        )

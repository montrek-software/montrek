import plotly.express as px
import plotly.graph_objects as go
from reporting.core.reporting_colors import ReportingColors
from reporting.core.reporting_data import ReportingTimelineData
from reporting.core.reporting_plots import ReportingPlotBase
import pandas as pd
import numpy as np

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
        # Validate start and end date columns are datetime-like
        for date_col in [reporting_data.start_date_col, reporting_data.end_date_col]:
            if not (np.issubdtype(df[date_col].dtype, np.datetime64) or pd.api.types.is_datetime64_any_dtype(df[date_col])):
                raise ValueError(f"Column '{date_col}' must be of datetime type.")
        # Validate item name column is string or categorical
        name_col = reporting_data.item_name_col
        if not (pd.api.types.is_string_dtype(df[name_col]) or pd.api.types.is_categorical_dtype(df[name_col])):
            raise ValueError(f"Column '{name_col}' must be of string or categorical type.")

    def get_figure(self, reporting_data: ReportingTimelineData) -> go.Figure:
        fig = px.timeline(
            reporting_data.timeline_df,
            x_start=reporting_data.start_date_col,
            x_end=reporting_data.end_date_col,
            y=reporting_data.item_name_col,
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

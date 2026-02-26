from datetime import date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from baseclasses.templatetags.colors import get_color
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
        timeline_df = reporting_data.timeline_df.copy()
        timeline_df[reporting_data.start_date_col] = pd.to_datetime(
            timeline_df[reporting_data.start_date_col]
        )
        timeline_df = timeline_df.sort_values(
            reporting_data.start_date_col, ascending=reporting_data.reversed_order
        ).reset_index(drop=True)

        fig = px.timeline(
            timeline_df,
            x_start=reporting_data.start_date_col,
            x_end=reporting_data.end_date_col,
            y=reporting_data.item_name_col,
            color=reporting_data.color_col,
            color_discrete_map=reporting_data.color_discrete_map,
            category_orders={
                reporting_data.item_name_col: (
                    timeline_df[reporting_data.item_name_col].drop_duplicates().tolist()
                )
            },
        )

        if reporting_data.report_date is not None:
            fig.add_vline(
                x=reporting_data.report_date,
                line_width=2,
                line_dash="dash",
                line_color=reporting_data.vline_color or ReportingColors.RED.hex,
            )

        return fig

    def update_axis_layout(self, reporting_data: ReportingTimelineData):
        if reporting_data.color_col is None:
            bar_color = reporting_data.bar_color or get_color("primary_light")
            self.figure.update_traces(marker_color=bar_color)
        self.figure.update_layout(
            showlegend=False,
            yaxis_title=None,
        )

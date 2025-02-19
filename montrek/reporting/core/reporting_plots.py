import tempfile
from typing import Any, List, Union

import plotly.graph_objects as go
from reporting.constants import ReportingPlotType
from reporting.core.reporting_colors import ReportingColors
from reporting.core.reporting_data import ReportingData
from reporting.core.reporting_mixins import ReportingChecksMixin
from reporting.core.reporting_protocols import ReportingElement


class ReportingPlot(ReportingElement, ReportingChecksMixin):
    def __init__(self, width: float = 1):
        self.width = width

    def generate(self, reporting_data: ReportingData) -> None:
        self._check_reporting_data(reporting_data)
        _x = self._set_x_axis(reporting_data)
        figure_data = self._get_figure_data(
            _x,
            reporting_data,
        )
        self.figure = go.Figure(data=figure_data)
        self.figure.update_layout(
            title_text=reporting_data.title,  # Adding Title
            title_font_color=ReportingColors.BLUE.hex,  # Customizing Title Color
            font=dict(
                family="Arial, sans-serif",
                size=14,
                color=ReportingColors.BLUE.hex,  # Customizing Font Color
            ),
            paper_bgcolor=ReportingColors.WHITE.hex,  # Customizing Background Color
            plot_bgcolor=ReportingColors.WHITE.hex,  # Customizing Plot Background Color
            xaxis=dict(
                color=ReportingColors.BLUE.hex,  # Axis text and line color
                gridcolor=ReportingColors.GREY.hex,  # Grid line color
                zerolinecolor=ReportingColors.GREY.hex,  # Zero line color
            ),
            yaxis=dict(
                color=ReportingColors.BLUE.hex,  # Axis text and line color
                gridcolor=ReportingColors.GREY.hex,  # Grid line color
                zerolinecolor=ReportingColors.GREY.hex,  # Zero line color
            ),
        )

    def to_html(self) -> str:
        return self.figure.to_html(full_html=False, include_plotlyjs="cdn")

    def to_latex(self) -> str:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        self.figure.write_image(temp_file.name)
        latex_str = "\\begin{figure}[H]\n"
        latex_str += (
            f"\\includegraphics[width={self.width}\\textwidth]{{{temp_file.name}}}\n"
        )
        latex_str += "\\end{figure}"
        return latex_str

    def _check_reporting_data(self, reporting_data: ReportingData) -> None:
        if len(reporting_data.y_axis_columns) != len(reporting_data.plot_types):
            raise ValueError("Number of y_axis_columns and plot_types must match")
        if not reporting_data.x_axis_is_index and reporting_data.x_axis_column is None:
            raise ValueError(
                "x_axis_column must be provided if x_axis_is_index is False"
            )

    def _set_x_axis(self, reporting_data: ReportingData) -> List[Any]:
        if reporting_data.x_axis_is_index:
            return reporting_data.data_df.index
        else:
            return reporting_data.data_df[reporting_data.x_axis_column]

    def _get_figure_data(
        self, _x: List[Any], reporting_data: ReportingData
    ) -> List[Any]:
        plot_types = self._set_plot_types(reporting_data)
        figure_data = []
        color_palette = ReportingColors().hex_color_palette()
        for i, (y_axis_column, plot_type) in enumerate(
            zip(reporting_data.y_axis_columns, plot_types)
        ):
            _y = reporting_data.data_df[y_axis_column]
            if plot_type == ReportingPlotType.BAR:
                figure_data.append(
                    go.Bar(
                        x=_x,
                        y=_y,
                        marker_color=color_palette[i],
                        name=y_axis_column,
                    )
                )
            elif plot_type == ReportingPlotType.LINE:
                figure_data.append(
                    go.Scatter(
                        x=_x,
                        y=_y,
                        marker_color=color_palette[i],
                    )
                )
            elif plot_type == ReportingPlotType.PIE:
                figure_data.append(
                    go.Pie(
                        labels=_x,
                        values=_y,
                        marker_colors=color_palette,
                        direction="clockwise",
                        sort=True,
                    )
                )
            else:
                raise ValueError(f"Plot type {plot_type} not supported")
        return figure_data

    def _set_plot_types(self, reporting_data: ReportingData) -> List[ReportingPlotType]:
        def _get_plot_type(
            plot_type: Union[str, ReportingPlotType],
        ) -> ReportingPlotType:
            if isinstance(plot_type, ReportingPlotType):
                return plot_type
            elif isinstance(plot_type, str):
                plot_type_str = plot_type.upper()
                if plot_type_str in dir(ReportingPlotType):
                    return getattr(ReportingPlotType, plot_type_str)
            else:
                raise ValueError(f"{plot_type} is no valid ReportingPlotType")

        return [_get_plot_type(plot_type) for plot_type in reporting_data.plot_types]

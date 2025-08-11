import hashlib
from typing import Any, Dict, List, Union

import plotly.graph_objects as go
from reporting.constants import WORKBENCH_PATH, ReportingPlotType
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
            margin={"l": 0, "r": 0},
        )

    def to_html(self) -> str:
        return self.figure.to_html(full_html=False, include_plotlyjs=False)

    def to_latex(self) -> str:
        # Generate a deterministic filename based on the plot data
        plot_json = self.figure.to_json()
        hash_digest = hashlib.sha256(plot_json.encode("utf-8")).hexdigest()[:16]
        filename = f"{hash_digest}.png"
        image_path = WORKBENCH_PATH / filename
        # Ensure the directory exists
        WORKBENCH_PATH.mkdir(parents=True, exist_ok=True)
        # Write the image if it does not already exist
        if not image_path.exists():
            self.figure.write_image(str(image_path), width=1000, height=500)

        # Build the LaTeX string
        latex_str = "\\begin{figure}[H]\n"
        latex_str += f"\\includegraphics[width=\\textwidth]{{{image_path}}}\n"
        latex_str += "\\end{figure}"

        return latex_str

    def to_json(self) -> dict[str, str | Any | None]:
        return {"reporting_plot": self.figure.to_json()}

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
        plot_parameters = self._set_plot_parameters(reporting_data)
        figure_data = []
        color_palette = ReportingColors().hex_color_palette()
        _y = None
        for i, (y_axis_column, plot_type) in enumerate(
            zip(reporting_data.y_axis_columns, plot_types)
        ):
            if plot_type == ReportingPlotType.BAR:
                _y = reporting_data.data_df[y_axis_column]
                figure_data.append(
                    go.Bar(
                        x=_x,
                        y=_y,
                        marker_color=color_palette[i],
                        name=y_axis_column,
                        **plot_parameters[i],
                    )
                )
            elif plot_type == ReportingPlotType.LINE:
                _y = reporting_data.data_df[y_axis_column]
                figure_data.append(
                    go.Scatter(
                        x=_x,
                        y=_y,
                        marker_color=color_palette[i],
                        name=y_axis_column,
                        **plot_parameters[i],
                    )
                )
            elif plot_type == ReportingPlotType.LINESTACK:
                if _y is None:
                    _y = reporting_data.data_df[y_axis_column]
                else:
                    _y += reporting_data.data_df[y_axis_column]
                figure_data.append(
                    go.Scatter(
                        x=_x,
                        y=_y,
                        marker_color=color_palette[i],
                        name=y_axis_column,
                        **plot_parameters[i],
                    )
                )
            elif plot_type == ReportingPlotType.PIE:
                _y = reporting_data.data_df[y_axis_column]
                figure_data.append(
                    go.Pie(
                        labels=_x,
                        values=_y,
                        marker_colors=color_palette,
                        direction="clockwise",
                        sort=True,
                        **plot_parameters[i],
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

    def _set_plot_parameters(
        self, reporting_data: ReportingData
    ) -> List[Dict[str, Any]]:
        if reporting_data.plot_parameters is None:
            return [{} for _ in range(len(reporting_data.plot_types))]
        return reporting_data.plot_parameters

from dataclasses import dataclass
from typing import Any

import pandas as pd
from networkx import DiGraph
from reporting.constants import ReportingPlotType


@dataclass
class ReportingDataBase:
    title: str


@dataclass
class ReportingData(ReportingDataBase):
    data_df: pd.DataFrame
    x_axis_column: str | None = None
    x_axis_is_index: bool = False
    y_axis_columns: list[str] | None = None
    plot_types: list[ReportingPlotType | str] | None = None
    plot_parameters: list[dict[str, Any]] | None = None


@dataclass
class ReportingNetworkData(ReportingDataBase):
    graph: DiGraph
    group_attr: str | None = None
    symbol_attr: str | None = None
    symbol_map: dict[str, str] | None = None
    marker_size: int = 20
    marker_line_width: int = 2
    fig_height: int = 400
    layout: str = "LR"
    link_attr: str = "link"


@dataclass
class ReportingTimelineData(ReportingDataBase):
    timeline_df: pd.DataFrame
    item_name_col: str
    start_date_col: str
    end_date_col: str

from dataclasses import dataclass
from typing import Any

import pandas as pd
from networkx import DiGraph
from reporting.constants import ReportingPlotType


@dataclass
class ReportingData:
    title: str
    data_df: pd.DataFrame
    x_axis_column: str | None = None
    x_axis_is_index: bool = False
    y_axis_columns: list[str] | None = None
    plot_types: list[ReportingPlotType | str] | None = None
    plot_parameters: list[dict[str, Any]] | None = None


@dataclass
class ReportingNetworkData:
    title: str
    graph: DiGraph

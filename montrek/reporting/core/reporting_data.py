from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd
from networkx import DiGraph
from reporting.constants import ReportingPlotType


@dataclass
class ReportingData:
    title: str
    data_df: Optional[pd.DataFrame] = None
    graph: Optional[DiGraph] = None
    x_axis_column: str | None = None
    x_axis_is_index: bool = False
    y_axis_columns: List[str] | None = None
    plot_types: List[ReportingPlotType | str] | None = None
    plot_parameters: List[Dict[str, Any]] | None = None

    def __post_init__(self):
        if self.data_df is None and self.graph is None:
            raise ValueError("You must provide either `data_df` or `graph`.")

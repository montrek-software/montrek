from typing import List
from dataclasses import dataclass
import pandas as pd
from reporting.constants import ReportingPlotType


@dataclass
class ReportingData:
    data_df: pd.DataFrame
    title: str
    x_axis_column: str = None
    x_axis_is_index: bool = False
    y_axis_columns: List[str] = None
    plot_types: List[ReportingPlotType] = None

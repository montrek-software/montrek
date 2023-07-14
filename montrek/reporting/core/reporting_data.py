from typing import List
from dataclasses import dataclass
import pandas as pd
from reporting.constants import ReportingPlotType


@dataclass
class ReportingData:
    data_df: pd.DataFrame
    x_axis_column: str
    y_axis_columns: List[str]
    plot_types: List[ReportingPlotType]


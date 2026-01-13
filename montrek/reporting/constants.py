from enum import Enum
from pathlib import Path

WORKBENCH_PATH = Path(__file__).resolve().parent / ".workbench"


class ReportingPlotType(Enum):
    NONE = 0
    LINE = 1
    BAR = 2
    PIE = 3
    SCATTER = 4
    HISTOGRAM = 5
    BOXPLOT = 6
    HEATMAP = 7
    LINESTACK = 8


class TextType(Enum):
    PLAIN = 0
    BOLD = 1
    ITALIC = 2
    UNDERLINE = 3
    STRIKETHROUGH = 4
    CODE = 5

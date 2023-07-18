from enum import Enum

class ReportingTextType(Enum):
    PLAIN = 0
    MARKDOWN = 1
    HTML = 2
    LATEX = 3


class ReportingPlotType(Enum):
    NONE = 0
    LINE = 1
    BAR = 2
    PIE = 3
    SCATTER = 4
    HISTOGRAM = 5
    BOXPLOT = 6
    HEATMAP = 7

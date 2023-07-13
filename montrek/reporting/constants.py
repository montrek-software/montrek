from enum import Enum

class ReportingTextType(Enum):
    PLAIN = 0
    MARKDOWN = 1
    HTML = 2
    LATEX = 3


class ReportingPlotType(Enum):
    LINE = 0
    BAR = 1
    PIE = 2
    SCATTER = 3
    HISTOGRAM = 4
    BOXPLOT = 5
    HEATMAP = 6

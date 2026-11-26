from enum import Enum


class PdfGenMethod(Enum):
    WEASYPRINT = "weasyprint"
    LATEX = "latex"


# Query parameter of a live row's refresh request, see LiveLabelTableElement.
LIVE_ROW_PARAM = "live_row"

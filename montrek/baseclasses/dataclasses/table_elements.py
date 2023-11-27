from dataclasses import dataclass
from reporting.core.reporting_colors import ReportingColors

def _get_value_color(value):
    return ReportingColors.RED if value < 0 else ReportingColors.DARK_BLUE

@dataclass
class TableElement:
    name: str

    def format(self, value):
        raise NotImplementedError


@dataclass
class StringTableElement(TableElement):
    attr: str

    def format(self, value):
        return f'<td style="text-align: left">{value}</td>'


@dataclass
class LinkTableElement(TableElement):
    url: str
    kwargs: dict
    icon: str
    hover_text: str


@dataclass
class EuroTableElement(TableElement):
    attr: str

    def format(self, value):
        color=_get_value_color(value)
        return f'<td style="text-align:right;color:{color};">{value:,.2f}&#x20AC;</td>'

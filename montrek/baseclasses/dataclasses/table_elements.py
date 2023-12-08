from dataclasses import dataclass
from decimal import Decimal
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
class LinkTextTableElement(TableElement):
    url: str
    kwargs: dict
    text: str
    hover_text: str

@dataclass
class FloatTableElement(TableElement):
    attr: str

    def format(self, value):
        if not isinstance(value, (int, float, Decimal)):
            return f'<td style="text-align:right;">{value}</td>'
        color = _get_value_color(value)
        return f'<td style="text-align:right;color:{color};">{value:,.3f}</td>'

@dataclass
class EuroTableElement(TableElement):
    attr: str

    def format(self, value):
        if not isinstance(value, (int, float, Decimal)):
            return f'<td style="text-align:right;">{value}</td>'
        color = _get_value_color(value)
        return f'<td style="text-align:right;color:{color};">{value:,.2f}&#x20AC;</td>'

@dataclass
class PercentTableElement(TableElement):
    attr: str

    def format(self, value):
        if not isinstance(value, (int, float, Decimal)):
            return f'<td style="text-align:right;">{value}</td>'
        color = _get_value_color(value)
        return f'<td style="text-align:right;color:{color};">{value:,.2%}</td>'

@dataclass
class DateTableElement(TableElement):
    attr: str

    def format(self, value):
        value = value.strftime("%d/%m/%Y")
        return f'<td style="text-align:left;">{value}</td>'

@dataclass
class BooleanTableElement(TableElement):
    attr: str

    def format(self, value):
        if value:
            return f'<td style="text-align:left;">&#x2713;</td>'
        return f'<td style="text-align:left;">&#x2717;</td>'

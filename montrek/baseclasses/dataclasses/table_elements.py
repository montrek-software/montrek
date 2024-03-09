from django.utils import timezone
from dataclasses import dataclass, field
from decimal import Decimal
from baseclasses.dataclasses.number_shortener import (
    NoShortening,
    NumberShortenerProtocol,
)
from reporting.core.reporting_colors import ReportingColors


def _get_value_color(value):
    return ReportingColors.RED if value < 0 else ReportingColors.DARK_BLUE


@dataclass
class TableElement:
    name: str

    def format(self, value):
        raise NotImplementedError

@dataclass
class AttrTableElement(TableElement):
    attr: str = field(default="")


@dataclass
class LinkTableElement(TableElement):
    url: str
    kwargs: dict
    icon: str
    hover_text: str


@dataclass
class LinkTextTableElement(LinkTableElement):
    pass

@dataclass
class StringTableElement(AttrTableElement):
    attr: str

    def format(self, value):
        return f'<td style="text-align: left">{value}</td>'


@dataclass
class NumberTableElement(AttrTableElement):
    attr: str
    shortener: NumberShortenerProtocol = NoShortening()

    def format(self, value):
        if not isinstance(value, (int, float, Decimal)):
            return f'<td style="text-align:left;">{value}</td>'
        color = _get_value_color(value)
        formatted_value = self._format_value(value)
        return f'<td style="text-align:right;color:{color};">{formatted_value}</td>'

    def _format_value(self, value) -> str:
        return self.shortener.shorten(value, "")


@dataclass
class FloatTableElement(NumberTableElement):
    attr: str
    shortener: NumberShortenerProtocol = NoShortening()

    def _format_value(self, value) -> str:
        return self.shortener.shorten(value, ",.3f")


@dataclass
class IntTableElement(NumberTableElement):
    attr: str
    shortener: NumberShortenerProtocol = NoShortening()

    def _format_value(self, value) -> str:
        value = round(value)
        return self.shortener.shorten(value, ",.0f")


@dataclass
class PercentTableElement(NumberTableElement):
    attr: str

    def _format_value(self, value) -> str:
        return f"{value:,.2%}"


@dataclasclass StringTableElement(AttrTableElement):):
    attr: str

    def format(self, value):
        if not isinstance(value, timezone.datetime):
            return f'<td style="text-align:left;">{value}</td>'
        value = value.strftime("%d/%m/%Y")
        return f'<td style="text-align:left;">{value}</td>'


@dataclass
cclass StringTableElement(AttrTableElement):):
    attr: str

    def format(self, value):
        if value:
            return '<td style="text-align:left;">&#x2713;</td>'
        return '<td style="text-align:left;">&#x2717;</td>'


@dataclass
class MoneyTableElement(NumberTableElement):
    attr: str
    shortener: NumberShortenerProtocol = NoShortening()

    @property
    def ccy_symbol(self) -> str:
        return ""

    def _format_value(self, value) -> str:
        value = self.shortener.shorten(value, ",.2f")
        return f"{value}{self.ccy_symbol}"


class EuroTableElement(MoneyTableElement):
    @property
    def ccy_symbol(self) -> str:
        return "&#x20AC;"


class DollarTableElement(MoneyTableElement):
    @property
    def ccy_symbol(self) -> str:
        return "&#0036;"

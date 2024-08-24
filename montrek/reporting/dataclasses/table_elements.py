import inspect
import pandas as pd
from typing import Any

from pandas.core.tools.datetimes import DateParseError
from baseclasses.dataclasses.alert import AlertEnum
from django.urls import NoReverseMatch, reverse
from django.template import Template, Context
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


def _get_value_color_latex(value):
    return "\\color{red}" if value < 0 else "\\color{darkblue}"


@dataclass
class TableElement:
    name: str

    def format(self, value):
        raise NotImplementedError

    def format_latex(self, value):
        return f" \\color{{black}} {value} &"

    def get_attribute(self, obj: Any, tag: str) -> str:
        raise NotImplementedError


@dataclass
class NoneTableElement(TableElement):
    attr: str = field(default="")

    def format(self):
        return '<td style="text-align: center">-</td>'


@dataclass
class AttrTableElement(TableElement):
    attr: str = field(default="")
    obj: Any = None

    def get_attribute(self, obj: Any, tag: str) -> str:
        attr = self.attr
        self.obj = obj
        if isinstance(obj, dict):
            value = obj.get(attr, attr)
        else:
            value = getattr(obj, attr, attr)
        if tag == "html":
            if value is None:
                return self.none_return_html(obj)
            return self.format(value)
        elif tag == "latex":
            if value is None:
                return " \\color{black} - &"
            return self.format_latex(value)
        return str(value)

    def none_return_html(self, obj: Any) -> str:
        return NoneTableElement(name=self.name, attr=self.attr).format()


@dataclass
class ExternalLinkTableElement(AttrTableElement):
    def format(self, value):
        return f'<td style="text-align:left;"><a href="{value}" target="_blank" title="{value}">{value}</a></td>'

    def format_latex(self, value):
        return f" \\url{{{value}}} &"


@dataclass  # noqa
class BaseLinkTableElement(TableElement):
    url: str
    kwargs: dict
    hover_text: str

    @staticmethod
    def get_dotted_attr_or_arg(obj, value):
        """Gets an attribute of an object dynamically from a string name"""
        """If the attribute is not found, then it is assumed to be an argument"""
        attrs = value.split(".")
        for attr in attrs:
            if isinstance(obj, dict):
                obj = obj.get(attr, None)
            else:
                obj = getattr(obj, attr, None)
        return obj

    def get_attribute(self, obj: Any, tag: str) -> str:
        if tag == "latex":
            value = self._get_link_text(obj)
            return self.format_latex(value)
        # TODO Update this such that _get_dotted_attr_or_arg is not used anymore
        kwargs = {
            key: BaseLinkTableElement.get_dotted_attr_or_arg(obj, value)
            for key, value in self.kwargs.items()
            if key != "filter"
        }
        kwargs = {key: str(value).replace("/", "_") for key, value in kwargs.items()}
        url_target = self.url
        try:
            url = reverse(
                url_target,
                kwargs=kwargs,
            )
        except NoReverseMatch:
            return "<td></td>"
        filter_field = self.kwargs.get("filter")
        if filter_field:
            filter_str = f"?filter_field={filter_field}&filter_lookup=in&filter_value={BaseLinkTableElement.get_dotted_attr_or_arg(obj, filter_field)}"
            url += filter_str
        link_text = self._get_link_text(obj)
        id_tag = url.replace("/", "_")
        hover_text = self.hover_text
        template_str = '<td><a id="id_{{ id_tag }}" href="{{ url }}" title="{{ hover_text }}">{{ link_text }}</a></td>'
        template = Template(template_str)
        context = {
            "url": url,
            "link_text": link_text,
            "url_target": url_target,
            "id_tag": id_tag,
            "hover_text": hover_text,
        }
        return template.render(Context(context))

    def _get_link_text(self, obj):
        raise NotImplementedError


@dataclass
class LinkTableElement(BaseLinkTableElement):
    icon: str

    def _get_link_text(self, obj):
        return Template(
            f'<span class="glyphicon glyphicon-{self.icon}"></span>'
        ).render(Context())


@dataclass
class LinkTextTableElement(BaseLinkTableElement):
    text: str

    def _get_link_text(self, obj):
        return BaseLinkTableElement.get_dotted_attr_or_arg(obj, self.text)


@dataclass
class StringTableElement(AttrTableElement):
    attr: str

    def format(self, value):
        return f'<td style="text-align: left">{value}</td>'


@dataclass
class AlertTableElement(AttrTableElement):
    attr: str

    def format(self, value):
        status = AlertEnum.get_by_description(value)
        return f'<td style="text-align: left;color:{status.color};">{value}</td>'


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

    def format_latex(self, value):
        if not isinstance(value, (int, float, Decimal)):
            return f"{value} &"
        color = _get_value_color_latex(value)
        formatted_value = self._format_value(value)
        return f"{color} {formatted_value} &"

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

    def format_latex(self, value) -> str:
        value = super().format_latex(value)
        return value.replace("%", "\\%")


@dataclass
class DateTableElement(AttrTableElement):
    attr: str

    def format(self, value):
        if not isinstance(value, timezone.datetime):
            return f'<td style="text-align:left;">{value}</td>'
        value = value.strftime("%d/%m/%Y")
        return f'<td style="text-align:left;">{value}</td>'


@dataclass
class DateYearTableElement(AttrTableElement):
    attr: str

    def format(self, value):
        try:
            value = pd.to_datetime(value)
            if pd.isnull(value):
                return '<td style="text-align:center;">-</td>'
            else:
                value = value.strftime("%Y")
        except DateParseError:
            value = value
        return f'<td style="text-align:left;">{value}</td>'


@dataclass
class BooleanTableElement(AttrTableElement):
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

    @property
    def ccy_symbol_latex(self) -> str:
        return ""

    def _format_value(self, value) -> str:
        value = self.shortener.shorten(value, ",.2f")
        return f"{value}{self.ccy_symbol}"

    def format_latex(self, value):
        formatted_value = super().format_latex(value)
        formatted_value = formatted_value.replace(
            self.ccy_symbol, self.ccy_symbol_latex
        )
        return formatted_value


class EuroTableElement(MoneyTableElement):
    @property
    def ccy_symbol(self) -> str:
        return "&#x20AC;"

    @property
    def ccy_symbol_latex(self) -> str:
        return "€"


class DollarTableElement(MoneyTableElement):
    @property
    def ccy_symbol(self) -> str:
        return "&#0036;"

    @property
    def ccy_symbol_latex(self) -> str:
        return "\\$"


@dataclass
class ImageTableElement(AttrTableElement):
    attr: str
    alt: str = "image"

    def format(self, value):
        return f'<td style="text-align:left;"><img src="{value}" alt="{self.alt}" style="width:100px;height:100px;"></td>'


class DateTimeTableElement(AttrTableElement):
    attr: str

    def format(self, value):
        if not isinstance(value, timezone.datetime):
            return f'<td style="text-align:left;">{value}</td>'
        value = value.strftime("%d/%m/%Y %H:%M:%S")
        return f'<td style="text-align:left;">{value}</td>'


@dataclass
class MethodNameTableElement(AttrTableElement):
    attr: str
    class_: type = object

    def format(self, value):
        func = getattr(self.class_, value)
        # Strip all decorator functions to get the to the original method.
        while hasattr(func, "__wrapped__"):
            func = func.__wrapped__
        doc = inspect.getdoc(func)
        doc = doc or ""
        return f'<td style="text-align: left" title="{doc}">{value}</td>'

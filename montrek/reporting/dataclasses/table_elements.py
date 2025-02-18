import inspect
import tempfile
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from urllib.parse import urlparse

import pandas as pd
import requests
from baseclasses.dataclasses.alert import AlertEnum
from baseclasses.dataclasses.number_shortener import (
    NoShortening,
    NumberShortenerABC,
)
from django.template import Context, Template
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from pandas.core.tools.datetimes import DateParseError
from reporting.core.reporting_colors import ReportingColors
from rest_framework import serializers

from reporting.core.text_converter import HtmlLatexConverter


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
        value_str = str(value)
        value_str = HtmlLatexConverter.convert(value_str)
        return f" \\color{{black}} {value_str} &"

    def get_attribute(self, obj: Any, tag: str) -> str:
        raise NotImplementedError


@dataclass
class NoneTableElement(TableElement):
    serializer_field_class = serializers.CharField
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
    serializer_field_class = serializers.CharField

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
        """
        Gets an attribute of an object dynamically from a string name.
        If the attribute is not found, then it is assumed to be an argument.
        """
        attrs = value.split(".")
        for attr in attrs:
            if isinstance(obj, dict):
                obj = obj.get(attr, None)
            else:
                obj = getattr(obj, attr, None)
        return obj

    def get_attribute(self, obj: Any, tag: str) -> str:
        link_text = self._get_link_text(obj)
        if tag == "latex":
            return self.format_latex(link_text)
        url_kwargs = self._get_url_kwargs(obj)
        url = self._get_url(obj, url_kwargs)
        link = self._get_link(url, link_text)
        return f"<td>{link}</td>"

    def _get_url_kwargs(self, obj: Any) -> dict:
        # TODO Update this such that _get_dotted_attr_or_arg is not used anymore
        kwargs = {
            key: self.get_dotted_attr_or_arg(obj, value)
            for key, value in self.kwargs.items()
            if key != "filter"
        }
        kwargs = {key: str(value).replace("/", "_") for key, value in kwargs.items()}
        return kwargs

    def _get_url(self, obj: Any, url_kwargs: dict) -> str:
        try:
            url = reverse(
                self.url,
                kwargs=url_kwargs,
            )
        except NoReverseMatch:
            return ""
        filter_field = self.kwargs.get("filter")
        if filter_field:
            filter_str = f"?filter_field={filter_field}&filter_lookup=in&filter_value={self.get_dotted_attr_or_arg(obj, filter_field)}"
            url += filter_str
        return url

    def _get_link(self, url: str, link_text: str) -> str:
        if not url:
            return ""
        id_tag = url.replace("/", "_")
        hover_text = self.hover_text
        template_str = '<a id="id_{{ id_tag }}" href="{{ url }}" title="{{ hover_text }}">{{ link_text }}</a>'
        template = Template(template_str)
        context = {
            "url": url,
            "link_text": link_text,
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
    serializer_field_class = serializers.CharField
    text: str

    def _get_link_text(self, obj):
        return BaseLinkTableElement.get_dotted_attr_or_arg(obj, self.text)


@dataclass
class LinkListTableElement(BaseLinkTableElement):
    serializer_field_class = serializers.CharField
    text: str
    list_attr: str
    list_kwarg: str
    out_separator: str = "<br>"

    def get_attribute(self, obj: Any, tag: str) -> str:
        if tag == "latex":
            value = self._get_link_text(obj)
            return self.format_latex(value)
        list_values = self.get_dotted_attr_or_arg(obj, self.list_attr)
        list_values = list_values.split(",") if list_values else []
        text_values = self.get_dotted_attr_or_arg(obj, self.text)
        text_values = text_values.split(",") if text_values else []
        assert len(list_values) == len(text_values)
        result = "<td>"
        for i, list_value in enumerate(list_values):
            url_kwargs = self._get_url_kwargs(obj)
            url_kwargs[self.list_kwarg] = list_value
            url = self._get_url(obj, url_kwargs)
            link_text = text_values[i]
            link = self._get_link(url, link_text)
            if i > 0:
                result += self.out_separator
            result += link
        result += "</td>"
        return result


@dataclass
class StringTableElement(AttrTableElement):
    serializer_field_class = serializers.CharField
    attr: str

    def format(self, value):
        return f'<td style="text-align: left">{value}</td>'


@dataclass
class TextTableElement(AttrTableElement):
    serializer_field_class = serializers.CharField
    attr: str

    def format(self, value):
        return f'<td style="text-align: left; white-space: pre-wrap;">{value}</td>'


@dataclass
class ListTableElement(AttrTableElement):
    serializer_field_class = serializers.CharField
    attr: str
    in_separator: str = ","
    out_separator: str = "<br>"

    def format(self, value):
        values = value.split(self.in_separator)
        out_value = self.out_separator.join(values)
        return f'<td style="text-align: left">{out_value}</td>'


@dataclass
class AlertTableElement(AttrTableElement):
    serializer_field_class = serializers.CharField
    attr: str

    def format(self, value):
        status = AlertEnum.get_by_description(value)
        return f'<td style="text-align: left;color:{status.color.hex};"><b>{value}</b></td>'


@dataclass
class NumberTableElement(AttrTableElement):
    attr: str
    shortener: NumberShortenerABC = NoShortening()

    def format(self, value):
        if not isinstance(value, (int, float, Decimal)):
            return f'<td style="text-align:left;">{value}</td>'
        color = _get_value_color(value)
        formatted_value = self._format_value(value)
        return f'<td style="text-align:right;color:{color.hex};">{formatted_value}</td>'

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
    serializer_field_class = serializers.FloatField
    attr: str
    shortener: NumberShortenerABC = NoShortening()

    def _format_value(self, value) -> str:
        return self.shortener.shorten(value, ",.3f")


@dataclass
class IntTableElement(NumberTableElement):
    serializer_field_class = serializers.IntegerField
    attr: str
    shortener: NumberShortenerABC = NoShortening()

    def _format_value(self, value) -> str:
        value = round(value)
        return self.shortener.shorten(value, ",.0f")


@dataclass
class PercentTableElement(NumberTableElement):
    serializer_field_class = serializers.FloatField
    attr: str

    def _format_value(self, value) -> str:
        return f"{value:,.2%}"

    def format_latex(self, value) -> str:
        value = super().format_latex(value)
        return value.replace("%", "\\%")


@dataclass
class ProgressBarTableElement(NumberTableElement):
    serializer_field_class = serializers.FloatField
    attr: str

    def format(self, value) -> str:
        per_value = value * 100
        return f"""<td><div class="bar-container"> <div class="bar" style="width: {per_value}%;"></div> <span class="bar-value">{value:,.2%}</span> </div></td>"""

    def format_latex(self, value) -> str:
        per_value = value * 100
        return f"\\progressbar{{ {per_value} }}{{ {per_value}\\% }} &"


@dataclass
class DateTableElement(AttrTableElement):
    serializer_field_class = serializers.DateField
    attr: str

    def format(self, value):
        if not isinstance(value, timezone.datetime):
            return f'<td style="text-align:left;">{value}</td>'
        value = value.strftime("%d/%m/%Y")
        return f'<td style="text-align:left;">{value}</td>'


@dataclass
class DateYearTableElement(AttrTableElement):
    serializer_field_class = serializers.DateField
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
    serializer_field_class = serializers.BooleanField
    attr: str

    def format(self, value):
        if value:
            return '<td style="text-align:left;">&#x2713;</td>'
        return '<td style="text-align:left;">&#x2717;</td>'


@dataclass
class MoneyTableElement(NumberTableElement):
    serializer_field_class = serializers.FloatField
    attr: str
    shortener: NumberShortenerABC = NoShortening()

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
    serializer_field_class = serializers.CharField
    attr: str
    alt: str = "image"

    def format(self, value):
        return f'<td style="text-align:left;"><img src="{value}" alt="{self.alt}" style="width:100px;height:100px;"></td>'

    def format_latex(self, value):
        def _return_string(value):
            return f"\\includegraphics[width=0.3\\textwidth]{{{value}}} &"

        # Check if value is a valid URL. If so, download the image and include it in the latex document.
        try:
            urlparse(value)
            is_url = True
        except ValueError:
            is_url = False
        if not is_url:
            return _return_string(value)
        response = requests.get(value)
        if response.status_code != 200:
            return f"Image not found: {value} &"
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix="." + value.split(".")[-1]
        )
        temp_file.write(response.content)
        temp_file_path = temp_file.name
        temp_file.close()
        value = temp_file_path
        return _return_string(value)


class DateTimeTableElement(AttrTableElement):
    serializer_field_class = serializers.DateTimeField
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

import datetime
import inspect
import tempfile
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any
from urllib.parse import urlparse
from django.template.base import mark_safe
from django.utils.html import format_html, format_html_join

import pandas as pd
import requests
from baseclasses.dataclasses.alert import AlertEnum
from baseclasses.dataclasses.number_shortener import NoShortening, NumberShortenerABC
from baseclasses.sanitizer import HtmlSanitizer
from django.core.exceptions import FieldDoesNotExist
from django.template import Context, Template
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from encrypted_fields import EncryptedCharField
from pandas.core.tools.datetimes import DateParseError
from reporting.core.reporting_colors import Color, ReportingColors
from reporting.core.text_converter import HtmlLatexConverter
from rest_framework import serializers


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

    def get_value(self, obj: Any) -> Any:
        raise NotImplementedError

    def get_value_len(self, obj: Any) -> int:
        return len(str(self.get_value(obj)))


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

    def get_attribute(self, obj: Any, tag: str = "html") -> str:
        self.obj = obj
        value = self.get_value(obj)
        if tag == "html":
            if pd.isna(value):
                return self.none_return_html(obj)
            return self.format(value)
        elif tag == "latex":
            if pd.isna(value):
                return " \\color{black} - &"
            return self.format_latex(value)
        return str(value)

    def get_value(self, obj: Any) -> Any:
        attr = self.attr
        if isinstance(obj, dict):
            value = obj.get(attr, attr)
        else:
            value = self._get_value_from_field(obj, attr)
        if isinstance(value, str):
            value = HtmlSanitizer().clean_html(value)
        return value

    def none_return_html(self, obj: Any) -> str:
        return NoneTableElement(name=self.name, attr=self.attr).format()

    def _get_value_from_field(self, obj: Any, attr: str) -> Any:
        try:
            field = obj._meta.get_field(attr)
        except FieldDoesNotExist:
            # Not a model field → just return the attribute (or the name if missing)
            return getattr(obj, attr, attr)
        value = getattr(obj, attr, attr)

        if isinstance(field, EncryptedCharField) and value is not None:
            value = "*" * len(str(value))
        return value


@dataclass
class ExternalLinkTableElement(AttrTableElement):
    serializer_field_class = serializers.CharField

    def format(self, value):
        return format_html(
            '<td style="text-align:left;"><a href="{value}" target="_blank" title="{value}">{value}</a></td>',
            value=value,
        )

    def format_latex(self, value):
        return f" \\url{{{value}}} &"


@dataclass  # noqa
class BaseLinkTableElement(TableElement):
    url: str
    kwargs: dict
    hover_text: str
    static_kwargs = {}

    def format_link(self, value, active: bool = False):
        if active:
            return format_html("<b>{value}</b>", value=value)
        return value

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

    def get_attribute(self, obj: Any, tag: str = "html") -> str:
        link_text = self.get_value(obj)
        if tag == "latex":
            return self.format_latex(link_text)
        if tag == "html":
            link = self.get_html_table_link_element(obj, link_text)
            return format_html("<td>{link}</td>", link=link)
        return link_text

    def get_html_table_link_element(
        self, obj: Any, link_text: str, *, active: bool = False
    ) -> str:
        url_kwargs = self._get_url_kwargs(obj)
        url = self._get_url(obj, url_kwargs)
        link = self._get_link(url, link_text)
        return f"{self.format_link(link, active)}"

    def get_value(self, obj):
        raise NotImplementedError

    def _get_url_kwargs(self, obj: Any) -> dict:
        # TODO Update this such that _get_dotted_attr_or_arg is not used anymore
        kwargs = {
            key: self.get_dotted_attr_or_arg(obj, value)
            for key, value in self.kwargs.items()
            if key != "filter"
        }
        kwargs = {key: str(value).replace("/", "_") for key, value in kwargs.items()}
        kwargs.update(self.static_kwargs)
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


@dataclass
class LinkTableElement(BaseLinkTableElement):
    icon: str
    static_kwargs: dict = field(default_factory=dict)

    def get_value(self, obj):
        if self.icon == "edit":
            icon = "pencil"
        else:
            icon = self.icon
        return Template(f'<span class="bi bi-{icon}"></span>').render(Context())


@dataclass
class LinkTextTableElement(BaseLinkTableElement):
    serializer_field_class = serializers.CharField
    text: str
    static_kwargs: dict = field(default_factory=dict)

    def get_value(self, obj):
        return BaseLinkTableElement.get_dotted_attr_or_arg(obj, self.text)


@dataclass
class LinkListTableElement(BaseLinkTableElement):
    serializer_field_class = serializers.CharField
    text: str
    list_attr: str
    list_kwarg: str
    in_separator: str = ";"
    out_separator: str = mark_safe("<br>")

    def get_attribute(self, obj: Any, tag: str = "html") -> str:
        values = self.get_value(obj)
        if tag == "latex":
            value = ",".join(link_text for _, link_text in values)
            return self.format_latex(value)
        if tag == "html":

            def link_iter():
                for list_value, link_text in values:
                    url_kwargs = self._get_url_kwargs(obj)
                    url_kwargs[self.list_kwarg] = list_value
                    url = self._get_url(obj, url_kwargs)
                    yield self._get_link(url, link_text)

            return format_html(
                "<td><div style='max-height: 300px; overflow-y: auto;'>{}</div></td>",
                format_html_join(
                    self.out_separator,
                    "{}",
                    ((link,) for link in link_iter()),
                ),
            )
        return "No tag"

    def get_value(self, obj) -> list:
        list_values = self.get_dotted_attr_or_arg(obj, self.list_attr)
        list_values = str(list_values).split(self.in_separator) if list_values else []
        text_values = self.get_dotted_attr_or_arg(obj, self.text)
        text_values = str(text_values).split(self.in_separator) if text_values else []
        assert len(list_values) == len(  # nosec b101
            text_values
        ), f"list_values: {list_values}, text_values: {text_values}"
        values = zip(list_values, text_values)
        values = sorted(values, key=lambda x: x[1])
        return values


@dataclass
class StringTableElement(AttrTableElement):
    serializer_field_class = serializers.CharField
    attr: str
    chunk_size: int = 56

    def format(self, value):
        return format_html('<td style="text-align: left">{value}</td>', value=value)

    def get_value(self, obj: Any) -> Any:
        value = super().get_value(obj)
        if pd.isna(value):
            return None
        value = str(value)
        if len(value) > self.chunk_size:
            return "<br>".join(self._chunk_text(value))
        return value

    def _chunk_text(self, text: str) -> list[str]:
        words = text.split()
        chunks, current = [], ""
        for w in words:
            if current and len(current) + len(w) + 1 > self.chunk_size:
                chunks.append(current)
                current = w
            else:
                current = (current + " " + w).strip()
        if current:
            chunks.append(current)
        return chunks


@dataclass
class TextTableElement(AttrTableElement):
    serializer_field_class = serializers.CharField
    attr: str

    def format(self, value):
        return format_html(
            '<td style="text-align: left; white-space: pre-wrap;">{value}</td>',
            value=value,
        )


@dataclass
class ListTableElement(AttrTableElement):
    serializer_field_class = serializers.CharField
    attr: str
    in_separator: str = ","
    out_separator: str = mark_safe("<br>")

    def format(self, value):
        values = value.split(self.in_separator)

        return format_html(
            '<td style="text-align: left">{}</td>',
            format_html_join(
                self.out_separator,
                "{}",
                ((v.strip(),) for v in values),
            ),
        )


@dataclass
class AlertTableElement(AttrTableElement):
    serializer_field_class = serializers.CharField
    attr: str

    def format(self, value):
        status = AlertEnum.get_by_description(value)
        status_color = status.color.hex
        return format_html(
            '<td style="text-align: left;color:{status_color};"><b>{value}</b></td>',
            status_color=status_color,
            value=value,
        )


@dataclass
class NumberTableElement(AttrTableElement):
    serializer_field_class = serializers.FloatField
    attr: str
    shortener: NumberShortenerABC = NoShortening()

    def format(self, value):
        if pd.isna(value):
            return '<td style="text-align:center;">-</td>'
        if not isinstance(value, (int, float, Decimal)):
            return f'<td style="text-align:left;">{value}</td>'
        color = _get_value_color(value).hex
        formatted_value = self._format_value(value)
        return format_html(
            '<td style="text-align:right;color:{color};">{formatted_value}</td>',
            color=color,
            formatted_value=formatted_value,
        )

    def format_latex(self, value):
        if not isinstance(value, (int, float, Decimal)):
            return f"{value} &"
        color = _get_value_color_latex(value)
        formatted_value = self._format_value(value)
        return f"{color} {formatted_value} &"

    def _format_value(self, value) -> str:
        return self.shortener.shorten(value, "")

    def get_value(self, obj: Any) -> Any:
        value = super().get_value(obj)
        if isinstance(value, Decimal):
            return float(value)
        return value


@dataclass
class FloatTableElement(NumberTableElement):
    serializer_field_class = serializers.FloatField
    attr: str
    shortener: NumberShortenerABC = NoShortening()

    def _format_value(self, value) -> str:
        return self.shortener.shorten(value, ",.3f")

    def get_value_len(self, obj: Any) -> int:
        return super().get_value_len(obj) + 4


@dataclass
class IntTableElement(NumberTableElement):
    serializer_field_class = serializers.IntegerField
    attr: str
    shortener: NumberShortenerABC = NoShortening()

    def _format_value(self, value) -> str:
        value = round(value)
        return self.shortener.shorten(value, ",.0f")

    def get_value(self, obj: Any) -> Any:
        value = super().get_value(obj)
        try:
            return int(value)
        except (TypeError, ValueError):
            return value


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

    def format(self, value: float):
        per_value = value * 100
        out_value = f"{value * 100: .2f}"

        return format_html(
            '<td><div class="bar-container"> <div class="bar" style="width: {per_value}%;"></div> <span class="bar-value">{value}%</span> </div></td>',
            per_value=per_value,
            value=out_value,
        )

    def format_latex(self, value) -> str:
        per_value = value * 100
        return f"\\progressbar{{ {per_value} }}{{ {per_value}\\% }} &"

    def get_value_len(self, obj: Any) -> int:
        return 14


@dataclass
class DateTableBaseElement(AttrTableElement):
    attr: str
    date_format = "%d/%m/%Y"

    def format(self, value):
        if isinstance(value, timezone.datetime):
            value = value.strftime(self.date_format)
        return format_html('<td style="text-align:left;">{value}</td>', value=value)

    def get_value(self, obj: Any) -> Any:
        value = super().get_value(obj)
        if isinstance(value, datetime.datetime) and not timezone.is_naive(value):
            value = timezone.make_naive(value)
        return value


class DateTableElement(DateTableBaseElement):
    serializer_field_class = serializers.DateField


class DateTimeTableElement(DateTableBaseElement):
    serializer_field_class = serializers.DateTimeField
    date_format = "%Y-%m-%d %H:%M:%S"


@dataclass
class DateYearTableElement(AttrTableElement):
    serializer_field_class = serializers.DateField
    attr: str

    def format(self, value):
        try:
            value = pd.to_datetime(value)
            if pd.isnull(value):
                return mark_safe('<td style="text-align:center;">-</td>')
            else:
                value = value.strftime("%Y")
        except DateParseError:
            return format_html('<td style="text-align:left;">{value}</td>', value=value)
        return format_html('<td style="text-align:left;">{value}</td>', value=value)


@dataclass
class BooleanTableElement(AttrTableElement):
    serializer_field_class = serializers.BooleanField
    attr: str

    def format(self, value):
        if value:
            return mark_safe('<td style="text-align:left;">&#x2713;</td>')
        return mark_safe('<td style="text-align:left;">&#x2717;</td>')


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
        return format_html(
            "{value}{ccy_symbol}", value=value, ccy_symbol=self.ccy_symbol
        )

    def format_latex(self, value):
        formatted_value = super().format_latex(value)
        formatted_value = formatted_value.replace(
            self.ccy_symbol, self.ccy_symbol_latex
        )
        return formatted_value


class EuroTableElement(MoneyTableElement):
    @property
    def ccy_symbol(self) -> str:
        return mark_safe("&#x20AC;")

    @property
    def ccy_symbol_latex(self) -> str:
        return "€"


class DollarTableElement(MoneyTableElement):
    @property
    def ccy_symbol(self) -> str:
        return mark_safe("&#0036;")

    @property
    def ccy_symbol_latex(self) -> str:
        return "\\$"


@dataclass
class ImageTableElement(AttrTableElement):
    serializer_field_class = serializers.CharField
    attr: str
    alt: str = "image"

    def format(self, value):
        alt = self.alt
        return format_html(
            '<td style="text-align:left;"><img src="{value}" alt="{alt}" style="width:100px;height:100px;"></td>',
            value=value,
            alt=alt,
        )

    def format_latex(self, value):
        def _return_string(value):
            return f"\\includegraphics[width=0.3\\textwidth]{{{value}}} &"

        # Check if value is a valid URL. If so, download the image and include it in the latex document.
        try:
            is_url = urlparse(value).scheme != ""
        except ValueError:
            is_url = False
        if not is_url:
            return _return_string(value)
        response = requests.get(value, timeout=10)
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


@dataclass
class MethodNameTableElement(AttrTableElement):
    attr: str
    class_: type = object
    serializer_field_class = serializers.CharField

    def format(self, value):
        func = getattr(self.class_, value)
        # Strip all decorator functions to get the to the original method.
        while hasattr(func, "__wrapped__"):
            func = func.__wrapped__
        doc = inspect.getdoc(func)
        doc = doc or ""
        return format_html(
            '<td style="text-align: left" title="{doc}">{value}</td>',
            doc=doc,
            value=value,
        )


class HistoryChangeState(Enum):
    OLD = "old"
    NEW = "new"
    NONE = "none"


ChangeMapType = dict[int, dict[str, HistoryChangeState]]


class HistoryStringTableElement(StringTableElement):
    def __init__(self, attr: str, name: str, change_map: ChangeMapType):
        super().__init__(name=name, attr=attr)
        self.change_map = change_map

    def format(self, value: Any) -> str:
        change_format = self._get_change_format()
        if change_format == HistoryChangeState.NONE:
            return super().format(value)
        if change_format == HistoryChangeState.OLD:
            red = ReportingColors.RED.hex
            return format_html(
                '<td style="text-align: left; color: {red}"><strong>{value}</strong></td>',
                red=red,
                value=value,
            )
        if change_format == HistoryChangeState.NEW:
            green = ReportingColors.DARK_GREEN.hex
            return format_html(
                '<td style="text-align: left; color: {green}"><strong>{value}</strong></td>',
                green=green,
                value=value,
            )

    def _get_change_format(self):
        obj_id = self.obj.id
        if obj_id not in self.change_map:
            return HistoryChangeState.NONE
        if self.attr not in self.change_map[obj_id]:
            return HistoryChangeState.NONE
        return self.change_map[obj_id][self.attr]


class ColorCodedStringTableElement(StringTableElement):
    def __init__(self, name: str, attr: str, color_codes: dict[str, Color]):
        self.color_codes = color_codes
        super().__init__(name, attr)

    def format(self, value):
        color = self.color_codes.get(value, ReportingColors.BLUE).hex
        return format_html(
            '<td style="text-align: left; color: {color}">{value}</td>',
            color=color,
            value=value,
        )

    def format_latex(self, value):
        value_str = str(value)
        value_str = HtmlLatexConverter.convert(value_str)
        color = self.color_codes.get(value, ReportingColors.BLUE)
        return f" \\color{{{color.name}}} {value_str} &"


class LabelTableElement(StringTableElement):
    def __init__(self, name: str, attr: str, color_codes: dict[str, Color]):
        self.color_codes = color_codes
        super().__init__(name, attr)

    def format(self, value):
        base_color = self.color_codes.get(value, ReportingColors.BLUE)
        font_color = ReportingColors.contrast_font_color(base_color).hex
        color = base_color.hex
        label_html = format_html(
            '<span class="badge" style="background-color:{color};color:{font_color};">{value}</span>',
            color=color,
            font_color=font_color,
            value=value,
        )
        return format_html(
            '<td style="text-align: left;">{label_html}</td>', label_html=label_html
        )

    def format_latex(self, value):
        value_str = str(value)
        value_str = HtmlLatexConverter.convert(value_str)

        color = self.color_codes.get(value, ReportingColors.BLUE)
        r, g, b = color.rgb()  # Must return 0–255 integers
        r /= 255
        g /= 255
        b /= 255

        font_color = ReportingColors.contrast_font_color(color)

        return (
            f"\\colorbox[rgb]{{{r:.3f},{g:.3f},{b:.3f}}}"
            f"{{\\textcolor[HTML]{{{font_color.hex.lstrip('#')}}}"
            f"{{\\textbf{{{value_str}}}}}}} &"
        )


class SecretStringTableElement(StringTableElement):
    def get_value(self, obj: Any) -> Any:
        value = super().get_value(obj)
        if value is None:
            return ""
        return "*" * min(56, len(str(value)))

import collections
import datetime
import inspect
import tempfile
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, ClassVar
from urllib.parse import urlparse

import pandas as pd
import requests
from baseclasses.dataclasses.alert import AlertEnum
from baseclasses.dataclasses.number_shortener import NoShortening, NumberShortenerABC
from baseclasses.sanitizer import HtmlSanitizer
from django.core.exceptions import FieldDoesNotExist
from django.template.base import mark_safe
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join, strip_tags
from encrypted_fields import EncryptedCharField
from pandas.core.tools.datetimes import DateParseError
from reporting.core.reporting_colors import Color, ReportingColors
from reporting.core.text_converter import HtmlLatexConverter
from reporting.dataclasses.display_field import DisplayField
from rest_framework import serializers

style_attrs_type = dict[str, str]
td_classes_type = list[str]


def _get_value_color(value):
    return ReportingColors.RED if value < 0 else ReportingColors.DARK_BLUE


def _get_value_color_latex(value):
    return "\\color{red}" if value < 0 else "\\color{darkblue}"


@dataclass
class TableElement:
    name: str
    style_attrs: ClassVar[style_attrs_type] = {}
    td_classes: ClassVar[td_classes_type] = ["text-start"]

    def format(self, value):
        raise NotImplementedError

    def format_latex(self, value):
        value_str = str(value)
        value_str = HtmlLatexConverter.convert(value_str)
        return f" \\color{{black}} {value_str} &"

    def get_attribute(self, obj: Any, tag: str = "html") -> str:
        if tag == "html":
            value = self.get_value(obj)
            return value
        elif tag == "latex":
            value = self.get_value(obj)
            if self.empty_value(value):
                return " \\color{black} - &"
            return self.format_latex(value)
        raise KeyError(f"Unknown tag {tag}")

    def get_value(self, obj: Any) -> Any:
        raise NotImplementedError

    def get_value_len(self, obj: Any) -> int:
        return len(str(self.get_value(obj)))

    def get_style_attrs(self, value: Any) -> style_attrs_type:
        # Method can be overwritten by daughter classes if styling changes depending on the value
        return self.style_attrs

    def get_style_attrs_str(self, value: Any) -> str:
        style_attrs = self.get_style_attrs(value)
        return self.format_style_attr(style_attrs)

    def format_style_attr(self, style_attrs: style_attrs_type) -> str:
        if len(style_attrs) == 0:
            return ""
        return "; ".join(f"{k}: {v}" for k, v in style_attrs.items()) + ";"

    def get_td_classes(self, value: Any) -> td_classes_type:
        # Method can be overwritten by daughter classes if styling changes depending on the value
        return self.td_classes

    def get_td_classes_str(self, value: Any) -> str:
        td_classes = self.get_td_classes(value)
        return self.format_td_classes(td_classes)

    def format_td_classes(self, td_classes: td_classes_type) -> str:
        return " ".join(td_classes)

    def get_display_field(self, obj: Any) -> DisplayField:
        value = self.get_attribute(obj, "html")

        table_element = NoneTableElement() if self.empty_value(value) else self
        return DisplayField(
            name=self.name,
            display_value=table_element.format(value),
            style_attrs_str=table_element.get_style_attrs_str(value),
            td_classes_str=table_element.get_td_classes_str(value),
        )

    def empty_value(self, value: Any) -> bool:
        # Check for scalar NA values
        try:
            if pd.isna(value):
                return True
        except (ValueError, TypeError):
            # pd.isna() fails on iterables, so check if it's an empty iterable
            if isinstance(value, collections.abc.Iterable) and not isinstance(
                value, str
            ):
                try:
                    return len(value) == 0
                except TypeError:
                    # No len() available, try to peek at the iterable
                    return not any(True for _ in value)
        return False


@dataclass
class NoneTableElement(TableElement):
    name: str = "None"
    serializer_field_class = serializers.CharField
    attr: str = field(default="")
    td_classes: ClassVar[td_classes_type] = ["text-center"]

    def format(self, value: Any) -> str:
        return "-"


@dataclass
class AttrTableElement(TableElement):
    attr: str = field(default="")
    obj: Any = None

    def get_value(self, obj: Any) -> Any:
        attr = self.attr
        if isinstance(obj, dict):
            value = obj.get(attr, attr)
        else:
            value = self._get_value_from_field(obj, attr)
        if isinstance(value, str):
            value = HtmlSanitizer().clean_html(value)
        return value

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
            '<a href="{value}" target="_blank" title="{value}">{value}</a>',
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

    def get_value(self, obj: Any) -> Any:
        self.obj = obj
        return self.get_link_text(obj)

    def format(self, value: Any) -> str:
        return self.get_html_table_link_element(self.obj, value)

    def format_latex(self, value):
        return super().format_latex(strip_tags(value))

    def get_html_table_link_element(
        self, obj: Any, link_text: str, *, active: bool = False
    ) -> str:
        url_kwargs = self._get_url_kwargs(obj)
        url = self._get_url(obj, url_kwargs)
        link = self._get_link(url, link_text)
        return f"{self.format_link(link, active)}"

    def get_link_text(self, obj):
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
        template_str = '<a id="id_{0}" href="{1}" title="{2}">{3}</a>'
        return format_html(template_str, id_tag, url, hover_text, link_text)


@dataclass
class LinkTableElement(BaseLinkTableElement):
    icon: str
    static_kwargs: dict = field(default_factory=dict)
    icon_latex_map: ClassVar[dict[str, str]] = {
        "pencil": "pencil",
        "edit": "pencil",
        "trash": "wastebasket",
    }

    def get_link_text(self, obj):
        if self.icon == "edit":
            icon = "pencil"
        else:
            icon = self.icon
        return icon

    def format(self, value: Any) -> str:
        icon_value = format_html('<span class="bi bi-{}"></span>', value)
        return self.get_html_table_link_element(self.obj, icon_value)

    def format_latex(self, value):
        latex_icon = self.icon_latex_map.get(value, "cross mark")
        return super().format_latex(f"\\twemoji{{{latex_icon}}}")


@dataclass
class LinkTextTableElement(BaseLinkTableElement):
    serializer_field_class = serializers.CharField
    text: str
    static_kwargs: dict = field(default_factory=dict)

    def get_link_text(self, obj):
        return BaseLinkTableElement.get_dotted_attr_or_arg(obj, self.text)


@dataclass
class LinkListTableElement(BaseLinkTableElement):
    serializer_field_class = serializers.CharField
    text: str
    list_attr: str
    list_kwarg: str
    in_separator: str = ";"
    out_separator: str = mark_safe("<br>")

    def link_iter(self, value, obj):
        for list_value, link_text in value:
            url_kwargs = self._get_url_kwargs(obj)
            url_kwargs[self.list_kwarg] = list_value
            url = self._get_url(obj, url_kwargs)
            yield self._get_link(url, link_text)

    def get_html_table_link_element(
        self, obj: Any, link_text: str, *, active: bool = False
    ) -> str:
        link_join = format_html_join(
            self.out_separator,
            "{}",
            ((link,) for link in self.link_iter(link_text, obj)),
        )
        return format_html(
            "<div style='max-height: 300px; overflow-y: auto;'>{}</div>", link_join
        )

    def get_link_text(self, obj) -> list:
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

    def format_latex(self, value):
        return " \\color{{black}} {} &".format(",".join([val[1] for val in value]))


@dataclass
class StringTableElement(AttrTableElement):
    serializer_field_class = serializers.CharField
    attr: str
    chunk_size: int = 56
    td_classes: ClassVar[td_classes_type] = ["text-start"]

    def format(self, value):
        return str(value)

    def get_value(self, obj: Any) -> Any:
        value = super().get_value(obj)
        if pd.isna(value):
            return None
        value = str(value)
        if len(value) > self.chunk_size:
            chunks = self._chunk_text(value)
            return format_html_join(
                mark_safe("<br>"), "{}", ((chunk,) for chunk in chunks)
            )
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
class TextTableElement(StringTableElement): ...


# TODO: Deprecate this class, since text wrapping is handled by StringTableElement


@dataclass
class ListTableElement(AttrTableElement):
    serializer_field_class = serializers.CharField
    attr: str
    in_separator: str = ","
    out_separator: str = mark_safe("<br>")
    td_classes: ClassVar[td_classes_type] = ["text-start"]

    def format(self, value):
        values = value.split(self.in_separator)

        return format_html_join(
            self.out_separator,
            "{}",
            ((v.strip(),) for v in values),
        )


@dataclass
class AlertTableElement(AttrTableElement):
    serializer_field_class = serializers.CharField
    attr: str
    td_classes: ClassVar[td_classes_type] = ["text-center"]

    def get_style_attrs(self, value: Any) -> style_attrs_type:
        status = AlertEnum.get_by_description(value)
        status_color = status.color.hex
        return {"color": status_color}

    def format(self, value):
        return format_html(
            "<b>{0}</b>",
            value,
        )


@dataclass
class NumberTableElement(AttrTableElement):
    serializer_field_class = serializers.FloatField
    attr: str
    shortener: NumberShortenerABC = NoShortening()
    numerical_type: type = float

    def get_display_field(self, obj: Any) -> DisplayField:
        value = self.get_attribute(obj, "html")
        display_value, td_classes, style_attrs = self._analyze_value(value)
        return DisplayField(
            name=self.name,
            display_value=display_value,
            style_attrs_str=self.format_style_attr(style_attrs),
            td_classes_str=self.format_td_classes(td_classes),
        )

    def _analyze_value(
        self, value: Any
    ) -> tuple[str, td_classes_type, style_attrs_type]:
        # returns (display_value, classes, style_attrs)
        if pd.isna(value):
            return "-", ["text-center"], {}

        if not isinstance(value, (int, float, Decimal)):
            return value, ["text-start"], {}

        formatted = self._format_value(value)
        color = _get_value_color(value).hex
        return formatted, ["text-end"], {"color": color}

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
        try:
            numerical_value = self.numerical_type(value)
        except (TypeError, ValueError):
            return value
        return numerical_value


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
    numerical_type: type = int
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
    td_classes: ClassVar[td_classes_type] = ["text-center"]

    def _format_value(self, value: float) -> str:
        per_value = value * 100
        out_value = f"{value * 100:.2f}"

        return format_html(
            '<div class="bar-container"> <div class="bar" style="width: {per_value}%;"></div> <span class="bar-value">{value}%</span> </div>',
            per_value=per_value,
            value=out_value,
        )

    def format_latex(self, value) -> str:
        per_value = value * 100
        return f"\\progressbar{{ {per_value} }}{{ {per_value:0.2f}\\% }} &"

    def get_value_len(self, obj: Any) -> int:
        return 14


@dataclass
class DateTableBaseElement(AttrTableElement):
    attr: str
    date_format = "%Y-%m-%d"
    td_classes: ClassVar[td_classes_type] = ["text-start"]

    def format(self, value):
        return self.format_date(value)

    def format_latex(self, value):
        return f" \\color{{black}} {self.format_date(value)} &"

    def format_date(self, value):
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.strftime(self.date_format)
        try:
            stripped_date = pd.to_datetime(value)
        except DateParseError:
            return value
        return stripped_date.strftime(self.date_format)

    def get_value(self, obj: Any) -> Any:
        value = super().get_value(obj)
        if value is None:
            return None
        if isinstance(value, datetime.datetime):
            if not timezone.is_naive(value):
                value = timezone.make_naive(value)
        return value


class DateTableElement(DateTableBaseElement):
    serializer_field_class = serializers.DateField


class DateTimeTableElement(DateTableBaseElement):
    serializer_field_class = serializers.DateTimeField
    date_format = "%Y-%m-%d %H:%M:%S"


class DateGermanTableElement(DateTableBaseElement):
    date_format = "%d.%m.%Y"


@dataclass
class DateYearTableElement(DateTableBaseElement):
    serializer_field_class = serializers.DateField
    date_format = "%Y"


@dataclass
class BooleanTableElement(AttrTableElement):
    serializer_field_class = serializers.BooleanField
    attr: str
    td_classes: ClassVar[td_classes_type] = ["text-center"]

    def format(self, value):
        if value:
            return mark_safe(
                '<span class="bi bi-check-circle-fill text-success"></span>'
            )
        return mark_safe('<span class="bi bi-x-circle-fill text-danger"></span>')

    def format_latex(self, value) -> str:
        if value:
            return "\\twemoji{white_check_mark} &"
        return "\\twemoji{cross mark} &"


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
    td_classes: ClassVar[td_classes_type] = ["text-start"]

    def format(self, value):
        alt = self.alt
        return format_html(
            '<img src="{value}" alt="{alt}" style="width:100px;height:100px;">',
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
            '<div title="{doc}">{value}</div>',
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
        self.change_format = HistoryChangeState.NONE

    def get_attribute(self, obj: Any, tag: str = "html") -> str:
        self.change_format = self._get_change_format(obj)
        return super().get_attribute(obj, tag)

    def get_style_attrs(self, value: Any) -> style_attrs_type:
        if self.change_format == HistoryChangeState.OLD:
            color = ReportingColors.RED.hex
        elif self.change_format == HistoryChangeState.NEW:
            color = ReportingColors.DARK_GREEN.hex
        else:
            color = ReportingColors.BLACK.hex
        return {"color": color}

    def get_td_classes(self, value: Any) -> td_classes_type:
        if self.change_format in (HistoryChangeState.OLD, HistoryChangeState.NEW):
            return ["fw-bold"]
        return []

    def _get_change_format(self, obj: Any):
        obj_id = obj.id
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
    td_classes: ClassVar[td_classes_type] = ["text-center"]

    def __init__(self, name: str, attr: str, color_codes: dict[str, Color]):
        self.color_codes = color_codes
        super().__init__(name, attr)

    def format(self, value):
        base_color = self.color_codes.get(value, ReportingColors.BLUE)
        font_color = ReportingColors.contrast_font_color(base_color).hex
        color = base_color.hex
        return format_html(
            '<span class="badge" style="background-color:{color};color:{font_color};">{value}</span>',
            color=color,
            font_color=font_color,
            value=value,
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

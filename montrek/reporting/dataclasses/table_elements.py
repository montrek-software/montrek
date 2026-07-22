import collections
import datetime
import inspect
import json
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, ClassVar, TypeVar
from urllib.parse import quote, urlencode, urlparse

import pandas as pd
import requests
from baseclasses.dataclasses.alert import AlertEnum
from baseclasses.dataclasses.number_shortener import NoShortening, NumberShortenerABC
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.template.base import mark_safe
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.html import strip_tags
from encrypted_fields import EncryptedCharField
from pandas.core.tools.datetimes import DateParseError
from reporting.core.reporting_colors import Color, ReportingColors
from reporting.core.text_converter import HtmlLatexConverter
from reporting.dataclasses.display_field import DisplayField
from rest_framework import serializers

from montrek.utils import SystemFormatting

type StyleAttrsType = dict[str, str]
type TdClassesType = list[str]
type ChangeMapType = dict[int, dict[str, HistoryChangeState]]
type ColorCodesType = dict[str, Color]

T = TypeVar("T")


def _get_value_color(value):
    return ReportingColors.RED if value < 0 else ReportingColors.DARK_BLUE


def _get_value_color_latex(value):
    return "\\color{red}" if value < 0 else "\\color{textdark}"


@dataclass
class TableElement:
    name: str
    attr: str = field(default="")
    hover_text: str | None = field(default=None)
    style_attrs: ClassVar[StyleAttrsType] = {}
    td_classes: ClassVar[TdClassesType] = ["text-start"]
    th_classes: ClassVar[TdClassesType | None] = None
    field_template: ClassVar[str | None] = None

    def format(self, _value):
        raise NotImplementedError

    def format_latex(self, value):
        value_str = str(value)
        value_str = HtmlLatexConverter.convert(value_str)
        value_str = HtmlLatexConverter.soft_hyphenate(value_str)
        return f" \\color{{textdark}} {value_str} &"

    def get_attribute(self, obj: Any, tag: str = "html") -> str | None:
        if tag == "html":
            value = self.get_value(obj)
            return value
        if tag == "latex":
            value = self.get_value(obj)
            if self.empty_value(value):
                return " \\color{textfaint} -- &"
            return self.format_latex(value)
        raise KeyError(f"Unknown tag {tag}")

    def get_value(self, _obj: Any) -> Any:
        raise NotImplementedError

    def get_value_len(self, obj: Any) -> int:
        return len(str(self.get_value(obj)))

    def get_style_attrs(self, _value: Any, _obj: Any) -> StyleAttrsType:
        # Method can be overwritten by daughter classes if styling changes depending on the value
        return self.style_attrs

    def get_style_attrs_str(self, value: Any, obj: Any) -> str:
        style_attrs = self.get_style_attrs(value, obj)
        return self.format_style_attr(style_attrs)

    def format_style_attr(self, style_attrs: StyleAttrsType) -> str:
        if len(style_attrs) == 0:
            return ""
        return "; ".join(f"{k}: {v}" for k, v in style_attrs.items()) + ";"

    def get_td_classes(self, _value: Any, _obj: Any) -> TdClassesType:
        # Method can be overwritten by daughter classes if styling changes depending on the value
        return self.td_classes

    def get_td_classes_str(self, value: Any, obj: Any) -> str:
        td_classes = self.get_td_classes(value, obj)
        return self.format_td_classes(td_classes)

    def format_td_classes(self, td_classes: TdClassesType) -> str:
        return " ".join(td_classes)

    @property
    def th_classes_str(self) -> str:
        # Header alignment follows the column's static cell alignment
        classes = self.th_classes if self.th_classes is not None else self.td_classes
        return self.format_td_classes(classes)

    def get_display_field(self, obj: Any) -> DisplayField:
        obj_value = self.get_attribute(obj, "html")
        table_element = (
            self.get_none_table_element() if self.empty_value(obj_value) else self
        )
        style_attrs_str = table_element.get_style_attrs_str(obj_value, obj)
        td_classes_str = table_element.get_td_classes_str(obj_value, obj)
        value = table_element.render_field_template(obj_value, obj)
        return DisplayField(
            name=self.name,
            display_value=table_element.format(value),
            style_attrs_str=style_attrs_str,
            td_classes_str=td_classes_str,
            hover_text=self.get_hover_text(obj, obj_value),
            value=obj_value,
        )

    def get_none_table_element(self):
        return NoneTableElement()

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

    def get_hover_text(self, _obj: Any, _value: Any) -> str | None:
        return self.hover_text

    def render_field_template(self, value: Any, obj: Any) -> str:
        if self.field_template is None:
            return value
        context_data = self.get_field_context_data(value, obj)
        context_data["value"] = value
        return render_to_string(
            f"tables/elements/{self.field_template}.html", context_data
        )

    def get_field_context_data(self, _value: Any, _obj: Any) -> dict[str, Any]:
        return {}

    @property
    def excel_format_str(self) -> str | None:
        return None


@dataclass
class NoneTableElement(TableElement):
    name: str = "None"
    serializer_field_class = serializers.CharField
    td_classes: ClassVar[TdClassesType] = ["text-center"]

    def format(self, _value: Any) -> str:
        return "-"


@dataclass
class AttrTableElement(TableElement):
    attr: str
    serializer_field_class = serializers.CharField
    obj: Any = None

    def get_value(self, obj: Any) -> Any:
        attr = self.attr
        return self._get_value_from_attr(obj, attr)

    def _get_value_from_attr(self, obj: Any, attr: str) -> Any:
        if isinstance(obj, dict):
            value = obj.get(attr, attr)
        else:
            value = self._get_value_from_field(obj, attr)
        return value

    def _get_value_from_field(self, obj: Any, attr: str) -> Any:
        try:
            field = obj._meta.get_field(attr)
        except (FieldDoesNotExist, AttributeError):
            # Not a model field, or obj has no _meta (e.g. SimpleNamespace)
            return getattr(obj, attr, attr)
        value = getattr(obj, attr, attr)

        if isinstance(field, EncryptedCharField) and value is not None:
            value = "*" * len(str(value))
        return value

    def format(self, value):
        return value


@dataclass
class ExternalLinkTableElement(AttrTableElement):
    field_template: ClassVar[str | None] = "external_link"

    def format(self, value):
        return value

    def get_value(self, obj: Any) -> Any:
        url = super().get_value(obj)
        # Ensure url is string-like before attempting to parse; otherwise, return as-is.
        if not isinstance(url, str | bytes):
            return url
        if not url:
            return url
        parsed = urlparse(url)
        missing_scheme = not parsed.scheme or (
            parsed.scheme
            and not parsed.netloc
            and "://" not in url
            and parsed.path.isdigit()
        )
        if missing_scheme:
            return "https://" + url
        return url

    def get_hover_text(self, obj: Any, value: Any) -> str | None:
        if value is None:
            return "No link"
        return value

    def format_latex(self, value):
        return f" \\url{{{value}}} &"


class GetDottetAttrsOrArgMixin:
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


@dataclass  # noqa
class BaseLinkTableElement(TableElement, GetDottetAttrsOrArgMixin):
    serializer_field_class = serializers.CharField
    url: str = field(default="")
    kwargs: dict = field(default_factory=dict)
    static_kwargs: dict = field(default_factory=dict)

    def get_attribute(self, obj: Any, tag: str = "html") -> str | None:
        if tag == "html":
            value = self.get_link(obj)
            return value
        if tag == "latex":
            value = self.get_value(obj)
            if self.empty_value(value):
                return " \\color{textfaint} -- &"
            return self.format_latex(value)
        raise KeyError(f"Unknown tag {tag}")

    def is_active(self, _value: Any, _obj: Any) -> bool:
        # May be overwritten with logic
        return False

    def get_td_classes(self, value: Any, obj: Any):
        td_classes = [*self.td_classes]
        if self.is_active(strip_tags(value).replace("\n", ""), obj):
            td_classes += ["fw-bold"]
        return td_classes

    def get_value(self, obj: Any) -> Any:
        link_text = self.get_link_text(obj)
        if link_text is None:
            return None
        return strip_tags(link_text)

    def format(self, value):
        return value

    def format_latex(self, value):
        return super().format_latex(strip_tags(value)).replace("\n", "")

    def get_link_text(self, _obj):
        raise NotImplementedError

    def get_url_kwargs(self, obj: Any) -> dict:
        kwargs = {
            key: self.get_dotted_attr_or_arg(obj, value)
            for key, value in self.kwargs.items()
            if key not in ["filter", "filter_field"]
        }
        kwargs = {key: str(value).replace("/", "_") for key, value in kwargs.items()}
        kwargs.update(self.static_kwargs)
        return kwargs

    def get_url(self, obj: Any) -> str:
        url_kwargs = self.get_url_kwargs(obj)
        try:
            url = reverse(
                self.url,
                kwargs=url_kwargs,
            )
        except NoReverseMatch:
            return ""
        filter_params = self.get_filter(obj)
        query = urlencode(filter_params, doseq=True, quote_via=quote)
        return f"{url}?{query}" if query else url

    def get_filter(self, obj: Any) -> dict[str, Any]:
        filter_value_field = self.kwargs.get("filter")
        if filter_value_field is None:
            return {}
        filter_field = self.kwargs.get("filter_field")
        if filter_field is None:
            filter_field = filter_value_field

        return {
            "filter_field": filter_field,
            "filter_lookup": "in",
            "filter_value": self.get_dotted_attr_or_arg(obj, filter_value_field),
        }

    def get_link(self, obj: Any) -> str | None:
        url = self.get_url(obj)
        if not url:
            return None
        id_tag = url.replace("/", "_")
        link_text = self.get_link_text(obj)
        context = {"id_tag": id_tag, "url": url, "link_text": link_text}
        return render_to_string("tables/elements/link.html", context)


@dataclass
class LinkTableElement(BaseLinkTableElement):
    td_classes: ClassVar[TdClassesType] = ["text-center"]
    icon: str = field(default="cross")
    static_kwargs: dict = field(default_factory=dict)
    icon_latex_map: ClassVar[dict[str, str]] = {
        "pencil": "pencil",
        "edit": "pencil",
        "trash": "wastebasket",
    }

    def get_link_text(self, _obj):
        context = {"value": self.get_icon(_obj)}
        return render_to_string("tables/elements/icon_link.html", context)

    def get_icon(self, _obj: Any) -> str:
        return "pencil" if self.icon == "edit" else self.icon

    def format_latex(self, _value):
        latex_icon = self.icon_latex_map.get(self.icon, "cross mark")
        return super().format_latex(f"\\twemoji{{{latex_icon}}}")


@dataclass
class HtmxLinkTableElement(LinkTableElement):
    """An icon link that triggers its action via HTMX instead of a full-page load.

    By default the response replaces the row the button lives in
    (``hx-target="closest tr"``, ``hx-swap="outerHTML"``), which lets a view
    swap a single re-rendered row in place. The plain ``href`` is kept as a
    progressive-enhancement fallback for when JavaScript/HTMX is unavailable.
    """

    hx_target: str = field(default="closest tr")
    hx_swap: str = field(default="outerHTML")
    td_classes: ClassVar[TdClassesType] = ["text-center"]

    def get_link(self, obj: Any) -> str | None:
        url = self.get_url(obj)
        if not url:
            return None
        context = {
            "id_tag": url.replace("/", "_"),
            "url": url,
            "icon": self.get_icon(obj),
            "hx_target": self.hx_target,
            "hx_swap": self.hx_swap,
        }
        context.update(self.get_extra_link_context(obj))
        return render_to_string("tables/elements/htmx_link.html", context)

    def get_extra_link_context(self, _obj: Any) -> dict[str, Any]:
        return {}


@dataclass
class InlineEditTableElement(HtmxLinkTableElement):
    """Pencil icon that opens an inline single-field edit form below its row.

    Point ``url`` at a ``MontrekInlineFieldEditView`` subclass: GET keeps the
    data row and adds an editor row directly below it, save/cancel swap the
    fresh data row back and the editor row removes itself. The plain ``href``
    fallback redirects non-HTMX visitors to the view's ``get_fallback_url()``.
    """

    icon: str = field(default="pencil-square")

    def get_extra_link_context(self, obj: Any) -> dict[str, Any]:
        # The editor row this trigger opens is ``inline-edit-{pk}`` (see
        # MontrekInlineFieldEditView.get_edit_row_id). Passing that id lets the
        # trigger remove an already-open editor for the same row before opening
        # a fresh one, so re-clicking the pencil can't orphan a second editor.
        pk = self.get_url_kwargs(obj).get("pk")
        return {"remove_editor_id": f"inline-edit-{pk}"}


@dataclass
class LinkTextTableElement(BaseLinkTableElement):
    text: str = field(default="")
    static_kwargs: dict = field(default_factory=dict)

    def get_link_text(self, obj):
        return BaseLinkTableElement.get_dotted_attr_or_arg(obj, self.text)


@dataclass
class LinkListTableElement(TableElement, GetDottetAttrsOrArgMixin):
    url: str = field(default="")
    static_kwargs: dict = field(default_factory=dict)
    serializer_field_class = serializers.CharField
    text: str = field(default="")
    list_attr: str = field(default="")
    list_kwarg: str = field(default="")
    in_separator: str | None = None
    field_template: ClassVar[str | None] = "link_list"

    def get_field_context_data(self, value: Any, obj: Any) -> dict[str, Any]:
        return {"link_list": self.get_link_list(value, obj)}

    def get_link_list(self, value, obj):
        list_values = self.get_list_values(obj)
        link_list = []
        kwargs = {self.list_kwarg: self.list_attr}

        for list_value, list_text in self._unique_list(
            zip(list_values, value, strict=True)
        ):
            link_list.append(
                LinkTextTableElement(
                    name=list_text,
                    text=self.text,
                    hover_text=self.hover_text,
                    url=self.url,
                    kwargs=kwargs,
                    static_kwargs=self.static_kwargs,
                ).get_display_field({self.text: list_text, self.list_attr: list_value})
            )
        return link_list

    def get_list_values(self, obj: Any) -> list[str]:
        list_values = self.get_dotted_attr_or_arg(obj, self.list_attr)
        if not list_values:
            return []
        if self.in_separator is None:
            return json.loads(str(list_values))
        return str(list_values).split(self.in_separator)

    def format(self, value):
        return value

    def get_value(self, obj: Any) -> list[str]:
        text_values = self.get_dotted_attr_or_arg(obj, self.text)
        if not text_values:
            return []
        if self.in_separator is None:
            return json.loads(str(text_values))
        return str(text_values).split(self.in_separator)

    def format_latex(self, value):
        return " \\color{{textdark}} {} &".format(",".join(self._unique_list(value)))

    @staticmethod
    def _unique_list(items: Iterable[T]) -> list[T]:
        return list(dict.fromkeys(items))


@dataclass
class StringTableElement(AttrTableElement):
    chunk_size: int = 56
    td_classes: ClassVar[TdClassesType] = ["text-start"]
    field_template: ClassVar[str | None] = "string"

    def get_field_context_data(self, value: Any, _obj: Any) -> dict[str, Any]:
        value = str(value)
        if len(value) > self.chunk_size:
            chunks = self._chunk_text(value)
            return {"chunks": chunks}
        return {"chunks": None}

    def format(self, value):
        return value

    def get_value(self, obj: Any) -> Any:
        value = super().get_value(obj)
        if pd.isna(value):
            return None
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


@dataclass
class ListTableElement(AttrTableElement):
    attr: str
    in_separator: str = ","
    out_separator: str = mark_safe("<br>")
    parse_as_json: bool = True
    td_classes: ClassVar[TdClassesType] = ["text-start"]
    field_template: ClassVar[str | None] = "list"

    def get_field_context_data(self, value: Any, _obj: Any) -> dict[str, Any]:
        values = self._parse_values(value)
        return {
            "values": [str(v).strip() for v in values],
            "out_separator": self.out_separator,
        }

    def _parse_values(self, value: Any) -> list[Any]:
        if not self.parse_as_json:
            return value.split(self.in_separator)
        if isinstance(value, list):
            return value
        return json.loads(value)


@dataclass
class AlertTableElement(AttrTableElement):
    attr: str
    td_classes: ClassVar[TdClassesType] = ["text-center"]
    field_template: ClassVar[str | None] = "alert"

    def get_style_attrs(self, value: Any, _obj: Any) -> StyleAttrsType:
        status = AlertEnum.get_by_description(value)
        status_color = status.color.hex
        return {"color": status_color}


@dataclass
class NumberTableElement(AttrTableElement):
    attr: str
    shortener: NumberShortenerABC = NoShortening()
    numerical_type: type = float
    serializer_field_class: ClassVar = serializers.FloatField
    th_classes: ClassVar[TdClassesType | None] = ["text-end"]
    _excel_decimal_places: ClassVar[int] = 2

    @property
    def excel_format_str(self) -> str:
        dec = self._excel_decimal_places
        if not dec:
            return "#,##0"
        return "#,##0." + dec * "0"

    def get_display_field(self, obj: Any) -> DisplayField:
        value = self.get_attribute(obj, "html")
        table_element = (
            self.get_none_table_element() if self.empty_value(value) else self
        )
        display_value = self._analyze_value(value)
        display_value = table_element.render_field_template(display_value, obj)
        return DisplayField(
            name=self.name,
            display_value=display_value,
            style_attrs_str=table_element.format_style_attr(
                self.get_style_attrs(value, obj)
            ),
            td_classes_str=table_element.format_td_classes(
                self.get_td_classes(value, obj)
            ),
            hover_text=self.get_hover_text(obj, value),
            value=value,
        )

    def get_td_classes(self, _value: Any, _obj: Any) -> TdClassesType:
        if pd.isna(_value):
            return ["text-center"]

        if not isinstance(_value, int | float | Decimal):
            return ["text-start"]
        return ["text-end"]

    def _analyze_value(self, value: Any) -> str:
        # returns a display string for the given value
        if pd.isna(value):
            return "-"

        if not isinstance(value, int | float | Decimal):
            return str(value)

        formatted = self._format_value(value)
        return formatted

    def get_style_attrs(self, _value: Any, _obj: Any) -> StyleAttrsType:
        if pd.isna(_value):
            return {}

        if not isinstance(_value, int | float | Decimal):
            return {}
        if _value < 0:
            return {"color": _get_value_color(_value).hex}
        # Non-negative numbers inherit the table text color (gold theme)
        return {}

    def format_latex(self, value):
        if not isinstance(value, int | float | Decimal):
            return f"{value} &"
        color = _get_value_color_latex(value)
        formatted_value = self._format_value(value)
        return f"{color} {formatted_value} &"

    def _format_value(self, value) -> str:
        return self.shortener.shorten(value, 2)

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
    _excel_decimal_places: ClassVar[int] = 3

    def _format_value(self, value) -> str:
        return self.shortener.shorten(value, 3)

    def get_value_len(self, obj: Any) -> int:
        return super().get_value_len(obj) + 4


@dataclass
class IntTableElement(NumberTableElement):
    serializer_field_class = serializers.IntegerField
    attr: str
    numerical_type: type = int
    shortener: NumberShortenerABC = NoShortening()
    _excel_decimal_places: ClassVar[int] = 0

    def _format_value(self, value) -> str:
        value = round(value)
        return self.shortener.shorten(value, 0)


@dataclass
class PercentTableElement(NumberTableElement):
    serializer_field_class = serializers.FloatField
    attr: str

    @property
    def excel_format_str(self) -> str:
        return "0.00%"

    def _format_value(self, value) -> str:
        return self.shortener.shorten(value * 100, 2) + "%"

    def get_value_len(self, obj: Any) -> int:
        value = self.get_value(obj)
        if not isinstance(value, int | float | Decimal):
            return super().get_value_len(obj)
        return len(self._format_value(value))

    def format_latex(self, value) -> str:
        value = super().format_latex(value)
        return value.replace("%", "\\%")


@dataclass
class ProgressBarTableElement(NumberTableElement):
    serializer_field_class = serializers.FloatField
    attr: str
    td_classes: ClassVar[TdClassesType] = ["text-center"]
    th_classes: ClassVar[TdClassesType | None] = ["text-center"]
    field_template: ClassVar[str | None] = "progress_bar"

    def get_field_context_data(self, value: Any, _obj: Any) -> dict[str, Any]:
        if settings.NUMBER_FORMATTING == SystemFormatting.DE:
            value = value.replace(".", "").replace(",", ".")
        value = float(value)
        per_value = value * 100
        out_value = f"{value * 100:.0f}"
        return {"per_value": str(per_value), "out_value": out_value}

    def format_latex(self, value) -> str:
        per_value = value * 100
        return f"\\progressbar{{ {per_value} }}{{ {per_value:0.2f}\\% }} &"

    def get_value_len(self, obj: Any) -> int:
        return 14


@dataclass
class DateTableBaseElement(AttrTableElement):
    attr: str
    td_classes: ClassVar[TdClassesType] = ["text-start"]

    @property
    def date_format(self) -> str:
        if (
            getattr(settings, "NUMBER_FORMATTING", SystemFormatting.EN)
            == SystemFormatting.DE
        ):
            return "%d.%m.%Y"
        return "%Y-%m-%d"

    def format(self, value):
        return self.format_date(value)

    def format_latex(self, value):
        return f" \\color{{textdark}} {self.format_date(value)} &"

    def format_date(self, value):
        if isinstance(value, (datetime.date | datetime.datetime)):
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
        if isinstance(value, datetime.datetime) and not timezone.is_naive(value):
            value = timezone.make_naive(value)
        return value


class DateTableElement(DateTableBaseElement):
    serializer_field_class = serializers.DateField


class DateTimeTableElement(DateTableBaseElement):
    serializer_field_class = serializers.DateTimeField

    @property
    def date_format(self) -> str:
        return super().date_format + " %H:%M:%S"


class DateGermanTableElement(DateTableBaseElement):
    @property
    def date_format(self) -> str:
        return "%d.%m.%Y"


@dataclass
class DateYearTableElement(DateTableBaseElement):
    serializer_field_class = serializers.DateField

    @property
    def date_format(self) -> str:
        return "%Y"


@dataclass
class BooleanTableElement(AttrTableElement):
    serializer_field_class = serializers.BooleanField
    attr: str
    td_classes: ClassVar[TdClassesType] = ["text-center"]
    field_template: ClassVar[str | None] = "bool"

    def format_latex(self, value) -> str:
        if value:
            return "\\twemoji{white_check_mark} &"
        return "\\twemoji{cross mark} &"


@dataclass
class MoneyTableElement(NumberTableElement):
    serializer_field_class = serializers.FloatField
    attr: str
    shortener: NumberShortenerABC = NoShortening()
    field_template: ClassVar[str | None] = "money"
    ccy_symbol: ClassVar[str] = ""
    latex_escape: ClassVar[bool] = False

    def get_field_context_data(self, _value: Any, _obj: Any) -> dict[str, Any]:
        return {"ccy_symbol": self.ccy_symbol}

    def _format_value(self, value) -> str:
        return self.shortener.shorten(value, 2)

    def get_value_len(self, obj: Any) -> int:
        value = self.get_value(obj)
        if not isinstance(value, int | float | Decimal):
            return super().get_value_len(obj)
        return len(self._format_value(value)) + len(self.ccy_symbol)

    def format_latex(self, value):
        formatted_value = super().format_latex(value)
        latex_ccy_symbol = (
            f"\\{self.ccy_symbol}" if self.latex_escape else self.ccy_symbol
        )
        formatted_value = formatted_value.replace(" &", f"{latex_ccy_symbol} &")
        return formatted_value


class EuroTableElement(MoneyTableElement):
    ccy_symbol: ClassVar[str] = "€"


class DollarTableElement(MoneyTableElement):
    latex_escape: ClassVar[bool] = True
    ccy_symbol: ClassVar[str] = "$"


@dataclass
class ImageTableElement(AttrTableElement):
    alt: str = "image"
    td_classes: ClassVar[TdClassesType] = ["text-start"]
    field_template: ClassVar[str | None] = "image"

    def get_field_context_data(self, _value: Any, _obj: Any) -> dict[str, Any]:
        return {"alt": self.alt}

    def format_latex(self, value):
        def _return_string(value):
            return f"\\includegraphics[width=0.3\\linewidth]{{{value}}} &"

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
    class_: type = object
    field_template: ClassVar[str | None] = "method_name"

    def get_field_context_data(self, value: Any, _obj: Any) -> dict[str, Any]:
        func = getattr(self.class_, value, None)
        # Strip all decorator functions to get the to the original method.
        while hasattr(func, "__wrapped__"):
            func = func.__wrapped__
        doc = inspect.getdoc(func)
        doc = doc or ""
        return {"doc": doc}


class HistoryChangeState(Enum):
    OLD = "old"
    NEW = "new"
    NONE = "none"


@dataclass
class HistoryStringTableElement(StringTableElement):
    change_map: ChangeMapType = field(default_factory=dict)

    def get_attribute(self, obj: Any, tag: str = "html") -> str:
        self.change_format = self._get_change_format(obj)
        return super().get_attribute(obj, tag)

    def get_style_attrs(self, _value: Any, _obj: Any) -> StyleAttrsType:
        if self.change_format == HistoryChangeState.OLD:
            color = ReportingColors.RED.hex
        elif self.change_format == HistoryChangeState.NEW:
            color = ReportingColors.DARK_GREEN.hex
        else:
            color = ReportingColors.BLACK.hex
        return {"color": color}

    def get_td_classes(self, _value: Any, _obj: Any) -> TdClassesType:
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


@dataclass
class ColorCodedStringTableElement(AttrTableElement):
    color_codes: ColorCodesType = field(default_factory=dict)

    def get_style_attrs(self, value: Any, _obj: Any) -> StyleAttrsType:
        color = self.color_codes.get(value, ReportingColors.BLUE).hex
        return {"color": color}

    def format_latex(self, value):
        value_str = str(value)
        value_str = HtmlLatexConverter.convert(value_str)
        color = self.color_codes.get(value, ReportingColors.BLUE)
        return f" \\color{{{color.name}}} {value_str} &"


@dataclass
class LabelTableElement(AttrTableElement):
    td_classes: ClassVar[TdClassesType] = ["text-center"]
    color_codes: ColorCodesType = field(default_factory=dict)
    field_template: ClassVar[str | None] = "label"

    def get_field_context_data(self, value: Any, _obj: Any) -> dict[str, Any]:
        base_color = self.color_codes.get(value, ReportingColors.BLUE)
        font_color = ReportingColors.contrast_font_color(base_color).hex
        color = base_color.hex
        return {"color": color, "font_color": font_color}

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


@dataclass
class CompData:
    num: int
    latex_val: str
    hover_text: str


def _circle_icon(color: str, start: str, end: str) -> str:
    return (
        f"\\tikz[baseline=-0.6ex]"
        f"{{\\fill[{color}] (0,0) circle (0.45em);"
        f" \\draw[->,white,line width=1.2pt,xshift=0.07em] {start} -- {end};}}"
    )


class CompValues(Enum):
    EQUAL = CompData(
        num=0,
        latex_val=_circle_icon("brightergreen", "(-0.22em,0)", "(0.15em,0)"),
        hover_text="=",
    )
    GREATER = CompData(
        num=1,
        latex_val=_circle_icon(
            "brighterorange", "(-0.17em,-0.17em)", "(0.14em,0.14em)"
        ),
        hover_text=">",
    )
    MUCH_GREATER = CompData(
        num=2,
        latex_val=_circle_icon("red", "(0,-0.22em)", "(0,0.15em)"),
        hover_text=">>",
    )
    LESS = CompData(
        num=-1,
        latex_val=_circle_icon(
            "brighterorange", "(-0.17em,0.17em)", "(0.14em,-0.14em)"
        ),
        hover_text="<",
    )
    MUCH_LESS = CompData(
        num=-2,
        latex_val=_circle_icon("red", "(0,0.22em)", "(0,-0.15em)"),
        hover_text="<<",
    )
    NONE = CompData(num=99, latex_val="", hover_text="Unknown")


class CompDataField(serializers.Field):
    """DRF field that serializes a :class:`CompData` instance as a plain dict.

    Accepts both a raw ``CompData`` dataclass instance and an already-converted
    ``dict`` (the latter arises when the value has been pre-processed by
    :class:`~reporting.modules.table_serializer.TableSerializer`).
    """

    _REQUIRED_KEYS = frozenset({"num", "latex_val", "hover_text"})

    def to_representation(self, value):
        if value is None:
            return None
        if isinstance(value, CompData):
            import dataclasses

            return dataclasses.asdict(value)
        if isinstance(value, dict):
            return value
        raise serializers.ValidationError(
            f"Expected a CompData instance or dict, got {type(value).__name__!r}."
        )

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError(
                f"Expected a dict, got {type(data).__name__!r}."
            )
        missing = self._REQUIRED_KEYS - data.keys()
        if missing:
            raise serializers.ValidationError(
                f"Missing required keys: {sorted(missing)}."
            )
        try:
            return CompData(
                num=int(data["num"]),
                latex_val=data["latex_val"],
                hover_text=data["hover_text"],
            )
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError(str(exc)) from exc


@dataclass
class ComparisonTableElement(AttrTableElement):
    comp_attr: str = field(default="")
    field_template: ClassVar[str | None] = "comparison"
    much_comp_limit: ClassVar[float] = 0.5
    serializer_field_class: ClassVar = CompDataField
    td_classes: ClassVar[TdClassesType] = ["align-top", "text-start", "ps-1"]

    def get_value(self, obj: Any) -> Any:
        value = super().get_value(obj)
        comp_value = self._get_value_from_attr(obj, self.comp_attr)
        if pd.isna(value) or pd.isna(comp_value):
            return CompValues.NONE.value
        if value == comp_value:
            return CompValues.EQUAL.value
        is_greater = value > comp_value
        is_much = (
            comp_value == 0
            or abs(value - comp_value) / comp_value > self.much_comp_limit
        )
        if is_greater:
            return (
                CompValues.MUCH_GREATER.value if is_much else CompValues.GREATER.value
            )
        return CompValues.MUCH_LESS.value if is_much else CompValues.LESS.value

    def get_value_len(self, _obj: Any) -> int:
        return 1

    def format_latex(self, value) -> str:
        return value.latex_val + " &"

    def get_hover_text(self, obj: Any, value: Any) -> str | None:
        start_value = super().get_value(obj)
        comp_value = self._get_value_from_attr(obj, self.comp_attr)
        return f"{start_value} {value.hover_text} {comp_value}"


@dataclass
class IconTableElement(AttrTableElement):
    icon: str = field(default="sign-stop")
    field_template: ClassVar[str | None] = "icon"
    icon_latex_map: ClassVar[dict[str, str]] = {
        "pencil": "pencil",
        "edit": "pencil",
        "trash": "wastebasket",
    }

    def get_value(self, _obj: Any) -> str:
        # Keep HTML icon names consistent with LinkTableElement / Bootstrap icon set.
        return "pencil" if self.icon == "edit" else self.icon

    def format_latex(self, value: str) -> str:
        latex_icon = self.icon_latex_map.get(value, "cross mark")
        return super().format_latex(f"\\twemoji{{{latex_icon}}}")


class SecretStringTableElement(StringTableElement):
    def get_value(self, obj: Any) -> Any:
        value = super().get_value(obj)
        if value is None:
            return ""
        return "*" * min(56, len(str(value)))

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


@dataclass
class TableElement:
    name: str

    def format(self, value):
        raise NotImplementedError

    def get_attribute(self, obj):
        raise NotImplementedError


@dataclass
class AttrTableElement(TableElement):
    attr: str = field(default="")

    def get_attribute(self, obj):
        attr = self.attr
        if isinstance(obj, dict):
            value = obj.get(attr, attr)
        else:
            value = getattr(obj, attr, attr)
        if value is None:
            return NoneTableElement().format()
        return self.format(value)


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

    def get_attribute(self, obj):
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
            filter_str = f"?filter_field={filter_field}__in&filter_value={BaseLinkTableElement.get_dotted_attr_or_arg(obj, filter_field)}"
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


class NoneTableElement:
    def format(self):
        return '<td style="text-align: center">-</td>'


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


@dataclass
class DateTableElement(AttrTableElement):
    attr: str

    def format(self, value):
        if not isinstance(value, timezone.datetime):
            return f'<td style="text-align:left;">{value}</td>'
        value = value.strftime("%d/%m/%Y")
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


@dataclass
class ImageTableElement(AttrTableElement):
    attr: str
    alt: str = "image"

    def format(self, value):
        return f'<td style="text-align:left;"><img src="{value}" alt="{self.alt}" style="width:100px;height:100px;"></td>'

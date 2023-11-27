from typing import Any
from django import template
from django.urls import reverse
from django.template import Template, Context
from baseclasses.dataclasses.view_classes import LinkTableElement

register = template.Library()


@register.filter(name="show_item")
def get_attribute(obj, table_element):
    if isinstance(table_element, LinkTableElement):
        return _get_link(obj, table_element)
    attr = table_element.attr
    value = _get_dotted_attr_or_arg(obj, attr)
    return _format_string(value)


def _get_dotted_attr_or_arg(obj, attr):
    """Gets an attribute of an object dynamically from a string name"""
    """If the attribute is not found, then it is assumed to be an argument"""
    attrs = attr.split(".")
    for attr in attrs:
        if attr.endswith("_set"):
            obj = getattr(obj, attr).first()
        else:
            obj = getattr(obj, attr, None)
        if obj is None:
            return attr
    return obj


def _get_link(obj, table_element):
    kwargs = {key: _get_dotted_attr_or_arg(obj, value) for key, value in table_element.kwargs.items()}
    kwargs = {key: str(value).replace("/", "_") for key, value in kwargs.items()}
    url_target = table_element.url
    url = reverse(
        url_target,
        kwargs=kwargs,
    )
    icon = table_element.icon
    id_tag = url.replace("/", "_")
    hover_text = table_element.hover_text
    template = Template(
        '<td><a id="id_{{ id_tag }}" href="{{ url }}" title="{{ hover_text }}"><span class="glyphicon glyphicon-{{ icon }}"></span></a></td>'
    )
    context = {
        "url": url,
        "icon": icon,
        "url_target": url_target,
        "id_tag": id_tag,
        "hover_text": hover_text,
    }
    return template.render(Context(context))


def _format_string(value):
    return f'<td style="text-align: left">{value}</td>'

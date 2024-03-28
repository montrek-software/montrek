from typing import Any
from django import template
from django.urls import NoReverseMatch, reverse
from django.template import Template, Context
from baseclasses.dataclasses import table_elements

register = template.Library()


@register.filter(name="show_item")
def get_attribute(obj, table_element):
    if isinstance(
        table_element,
        (table_elements.LinkTableElement, table_elements.LinkTextTableElement),
    ):
        return _get_link(obj, table_element)
    attr = table_element.attr
    value = getattr(obj, attr, attr)
    if not value:
        return table_elements.NoneTableElement().format()
    return table_element.format(value)


def _get_dotted_attr_or_arg(obj, attr):
    """Gets an attribute of an object dynamically from a string name"""
    """If the attribute is not found, then it is assumed to be an argument"""
    attrs = attr.split(".")
    for attr in attrs:
        obj = getattr(obj, attr, None)
        if obj is None:
            return attr
    return obj


def _get_link(obj, table_element):
    # TODO Update this such that _get_dotted_attr_or_arg is not used anymore
    kwargs = {
        key: _get_dotted_attr_or_arg(obj, value)
        for key, value in table_element.kwargs.items()
    }
    kwargs = {key: str(value).replace("/", "_") for key, value in kwargs.items()}
    url_target = table_element.url
    try:
        url = reverse(
            url_target,
            kwargs=kwargs,
        )
    except NoReverseMatch:
        return "<td></td>"
    if isinstance(table_element, table_elements.LinkTextTableElement):
        link_text = _get_dotted_attr_or_arg(obj, table_element.text)
    else:
        link_text = Template(
            '<span class="glyphicon glyphicon-{{ icon }}"></span>'
        ).render(Context({"icon": table_element.icon}))
    id_tag = url.replace("/", "_")
    hover_text = table_element.hover_text
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

from typing import Any
from django import template
from django.urls import NoReverseMatch, reverse
from django.template import Template, Context
from reporting.dataclasses import table_elements

register = template.Library()


@register.filter(name="show_item")
def get_attribute(obj, table_element):
    if isinstance(
        table_element,
        (table_elements.LinkTableElement, table_elements.LinkTextTableElement),
    ):
        return _get_link_attribute(obj, table_element)
    elif isinstance(table_element, table_elements.LinkListTableElement):
        return _get_link_list_attribute(obj, table_element)

    attr = table_element.attr
    if isinstance(obj, dict):
        value = obj.get(attr, attr)
    else:
        value = getattr(obj, attr, attr)
    if value is None:
        return table_elements.NoneTableElement(name="").format()
    return table_element.format(value)


def _get_dotted_attr_or_arg(obj, attr):
    """Gets an attribute of an object dynamically from a string name"""
    """If the attribute is not found, then it is assumed to be an argument"""
    attrs = attr.split(".")
    for attr in attrs:
        if isinstance(obj, dict):
            obj = obj.get(attr, None)
        else:
            obj = getattr(obj, attr, None)
    return obj


def _get_url_kwargs(table_element, obj: Any) -> dict:
    # TODO Update this such that _get_dotted_attr_or_arg is not used anymore
    kwargs = {
        key: _get_dotted_attr_or_arg(obj, value)
        for key, value in table_element.kwargs.items()
        if key != "filter"
    }
    kwargs = {key: str(value).replace("/", "_") for key, value in kwargs.items()}
    return kwargs


def _get_url(table_element, obj: Any, url_kwargs: dict) -> str:
    try:
        url = reverse(
            table_element.url,
            kwargs=url_kwargs,
        )
    except NoReverseMatch:
        return ""
    filter_field = table_element.kwargs.get("filter")
    if filter_field:
        filter_str = f"?filter_field={filter_field}&filter_lookup=in&filter_value={_get_dotted_attr_or_arg(obj, filter_field)}"
        url += filter_str
    return url


def _get_link(table_element, url: str, link_text: str) -> str:
    if not url:
        return ""
    id_tag = url.replace("/", "_")
    hover_text = table_element.hover_text
    template_str = '<a id="id_{{ id_tag }}" href="{{ url }}" title="{{ hover_text }}">{{ link_text }}</a>'
    template = Template(template_str)
    context = {
        "url": url,
        "link_text": link_text,
        "id_tag": id_tag,
        "hover_text": hover_text,
    }
    return template.render(Context(context))


def _get_link_attribute(obj, table_element):
    # TODO Update this such that _get_dotted_attr_or_arg is not used anymore
    link_text = _get_dotted_attr_or_arg(obj, table_element.text)
    url_kwargs = _get_url_kwargs(table_element, obj)
    url = _get_url(table_element, obj, url_kwargs)
    if isinstance(table_element, table_elements.LinkTextTableElement):
        link_text = _get_dotted_attr_or_arg(obj, table_element.text)
        link_text = "" if link_text is None else link_text
    else:
        link_text = Template(
            '<span class="glyphicon glyphicon-{{ icon }}"></span>'
        ).render(Context({"icon": table_element.icon}))
    link = _get_link(table_element, url, link_text)
    return link


def _get_link_list_attribute(obj, table_element):
    list_values = _get_dotted_attr_or_arg(obj, table_element.list_attr)
    list_values = list_values.split(",") if list_values else []
    text_values = _get_dotted_attr_or_arg(obj, table_element.text)
    text_values = text_values.split(",") if text_values else []
    assert len(list_values) == len(text_values)
    result = "<td>"
    for i, list_value in enumerate(list_values):
        url_kwargs = _get_url_kwargs(table_element, obj)
        url_kwargs[table_element.list_kwarg] = list_value
        url = _get_url(table_element, obj, url_kwargs)
        link_text = text_values[i]
        link = _get_link(table_element, url, link_text)
        result += f"{link}{table_element.out_separator}"
    result += "</td>"
    return result

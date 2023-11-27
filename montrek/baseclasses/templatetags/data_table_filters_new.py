from typing import Any
from django import template
from django.urls import reverse
from django.template import Template, Context

register = template.Library()

@register.filter(name='show_item')
def get_attribute(obj, table_element):
    """Gets an attribute of an object dynamically from a string name"""
    attr = table_element.attr
    value = _get_dotted_attr_or_arg(obj, attr)
    return _return_value(value)


def _get_dotted_attr_or_arg(obj, attr):
    """Gets an attribute of an object dynamically from a string name"""
    """If the attribute is not found, then it is assumed to be an argument"""
    attrs = attr.split('.')
    for attr in attrs:
        if attr.endswith('_set'):
            obj = getattr(obj, attr).first()
        else:
            obj = getattr(obj, attr, None)
        if obj is None:
            return attr
    return obj

def _return_value(value):
    """Returns a value based on the field descriptor"""
    is_number = str(value).replace('.','').replace('-','').isdecimal()
    align = 'right' if is_number  else 'left'
    return f"<td style=\"text-align: {align}\">{value}</td>"

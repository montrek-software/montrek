from typing import Any
from django import template
from django.urls import reverse
from django.template import Template, Context

register = template.Library()

@register.filter(name='show_item')
def get_attribute(obj, field_descriptor):
    """Gets an attribute of an object dynamically from a string name"""
    if 'attr' in field_descriptor: 
        attrs = field_descriptor['attr'].split('.')
        for attr in attrs:
            obj = _get_dotted_attr(obj, attr)
            if obj is None:
                return ""
        return obj
    if 'link' in field_descriptor:
        kwargs = field_descriptor['link']['kwargs']
        kwargs = {key: _get_dotted_attr(obj, value) for key, value in kwargs.items()}
        url = reverse(field_descriptor['link']['url'], 
                      kwargs=kwargs,
                     )
        icon = field_descriptor['link']['icon'] 
        template = Template('<a id="id_transaction_view_" href="{{ url }}"><span class="glyphicon glyphicon-{{ icon }}"></span></a>')
        context = {'url': url,
                   'icon': icon,}
        return template.render(Context(context))
    return ""

def _get_dotted_attr(obj, attr):
    """Gets an attribute of an object dynamically from a string name"""
    attrs = attr.split('.')
    for attr in attrs:
        obj = getattr(obj, attr, None)
        if obj is None:
            return ""
    return obj

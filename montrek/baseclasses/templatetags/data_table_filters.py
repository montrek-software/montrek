from typing import Any
from django import template
from django.urls import reverse
from django.template import Template, Context

register = template.Library()

@register.filter(name='show_item')
def get_attribute(obj, field_descriptor):
    """Gets an attribute of an object dynamically from a string name"""
    if 'attr' in field_descriptor: 
        attr = field_descriptor['attr']
        value = _get_dotted_attr_or_arg(obj, attr)
        return _return_value(value, field_descriptor)

    if 'divid' in field_descriptor:
        values = []
        for attr in field_descriptor['divid']:
            values.append(_get_dotted_attr_or_arg(obj, attr))
        value = values[0]/values[1]
        return _return_value(value, field_descriptor)

    if 'link' in field_descriptor:
        kwargs = field_descriptor['link']['kwargs']
        kwargs = {key: _get_dotted_attr_or_arg(obj, value) for key, value in kwargs.items()}
        kwargs = {key: str(value).replace('/', '_') for key, value in kwargs.items()}
        url_target = field_descriptor['link']['url']
        url = reverse(url_target, 
                      kwargs=kwargs,
                     )
        icon = field_descriptor['link']['icon'] 
        id_tag = url.replace('/', '_')
        hover_text = field_descriptor['link']['hover_text']
        template = Template('<td><a id="id_{{ id_tag }}" href="{{ url }}" title="{{ hover_text }}"><span class="glyphicon glyphicon-{{ icon }}"></span></a></td>')
        context = {'url': url,
                   'icon': icon,
                   'url_target': url_target,
                   'id_tag': id_tag,
                   'hover_text': hover_text,
                  }
        return template.render(Context(context))

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

def _return_value(value, field_descriptor):
    """Returns a value based on the field descriptor"""
    align = 'right' if str(value).replace('.','').isdecimal() else 'left'
    if 'format' in field_descriptor:
        iformat = field_descriptor['format']
        value = iformat.format(value)
    return f"<td style=\"text-align: {align}\">{value}</td>"

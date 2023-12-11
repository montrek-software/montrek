from django import template
from django.utils.safestring import mark_safe
from baseclasses.views import navbar

register = template.Library()

@register.simple_tag(takes_context=True)
def include_navbar(context):
    request = context['request']
    response = navbar(request)
    return mark_safe(response.content.decode('utf-8'))

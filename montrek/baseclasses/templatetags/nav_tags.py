from django import template
from django.http import HttpRequest
from baseclasses.views import navbar

register = template.Library()

@register.simple_tag(takes_context=True)
def include_navbar(context):
    request = HttpRequest()
    return navbar(request).content

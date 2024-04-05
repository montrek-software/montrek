from django import template
from django.utils.safestring import mark_safe
from baseclasses.views import navbar, links, client_logo

register = template.Library()


@register.simple_tag(takes_context=True)
def include_navbar(context):
    request = context["request"]
    response = navbar(request)
    return mark_safe(response.content.decode("utf-8"))


@register.simple_tag(takes_context=True)
def include_links(context):
    request = context["request"]
    response = links(request)
    return mark_safe(response.content.decode("utf-8"))


@register.simple_tag(takes_context=True)
def include_client_logo(context):
    request = context["request"]
    response = client_logo(request)
    return mark_safe(response.content.decode("utf-8"))

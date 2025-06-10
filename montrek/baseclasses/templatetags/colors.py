from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def get_color(name):
    color_scheme = {
        "primary": settings.PRIMARY_COLOR,
        "secondary": settings.SECONDARY_COLOR,
    }
    return color_scheme.get(name, "#000000")

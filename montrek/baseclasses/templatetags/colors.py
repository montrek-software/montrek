from functools import cache

from django import template
from django.conf import settings
from reporting.core.reporting_colors import Color, ReportingColors

register = template.Library()


@cache
def _get_color_scheme():
    primary_color = Color("primary", settings.PRIMARY_COLOR)
    secondary_color = Color("secondary", settings.SECONDARY_COLOR)
    return {
        "primary": primary_color.hex,
        "secondary": secondary_color.hex,
        "primary_light": ReportingColors.lighten_color(primary_color).hex,
        "secondary_light": ReportingColors.lighten_color(secondary_color).hex,
    }


@register.simple_tag
def get_color(name):
    return _get_color_scheme().get(name, "#000000")

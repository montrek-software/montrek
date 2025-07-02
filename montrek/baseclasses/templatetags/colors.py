from django import template
from django.conf import settings
from reporting.core.reporting_colors import Color, ReportingColors

register = template.Library()


@register.simple_tag
def get_color(name):
    primary_color = Color("primary", settings.PRIMARY_COLOR)
    secondary_color = Color("secondary", settings.SECONDARY_COLOR)
    color_scheme = {
        "primary": primary_color.hex,
        "secondary": secondary_color.hex,
    }
    color_scheme["primary_light"] = ReportingColors.lighten_color(primary_color).hex
    color_scheme["secondary_light"] = ReportingColors.lighten_color(secondary_color).hex
    return color_scheme.get(name, "#000000")

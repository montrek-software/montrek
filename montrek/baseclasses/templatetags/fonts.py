from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def get_font_name() -> str:
    """The configured typeface, or "" to keep the theme's own font stack."""
    return settings.FONT_NAME

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def get_custom_css() -> list[str]:
    """Static paths of the client stylesheets that override the gold theme."""
    return settings.CUSTOM_CSS

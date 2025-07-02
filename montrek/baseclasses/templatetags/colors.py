from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def get_color(name):
    color_scheme = {
        "primary": settings.PRIMARY_COLOR,
        "secondary": settings.SECONDARY_COLOR,
    }
    color_scheme["primary_light"] = lighten_color(color_scheme["primary"])
    color_scheme["secondary_light"] = lighten_color(color_scheme["secondary"])
    return color_scheme.get(name, "#000000")


def lighten_color(hex_color, factor=0.9):
    """
    Lighten the given hex color by a factor (0 < factor < 1).
    `factor` is how much closer to white the color should move.
    """
    hex_color = hex_color.lstrip("#")
    r, g, b = [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]

    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)

    return "#{:02x}{:02x}{:02x}".format(r, g, b)

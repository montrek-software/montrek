from django import template

register = template.Library()


@register.simple_tag
def get_color(name):
    color_scheme = {
        "primary": "green",
        "secondary": "red",
    }
    return color_scheme.get(name, "#000000")

"""Startup check for the client stylesheets in ``CUSTOM_CSS``.

A stylesheet the static finders cannot locate is linked anyway and answered
with a 404, so a mistyped path would silently leave the app in the plain gold
theme. It is reported here instead.
"""

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.checks import Tags, Warning, register


@register(Tags.staticfiles)
def check_custom_css_paths(app_configs=None, **kwargs) -> list[Warning]:
    return [
        Warning(
            f"CUSTOM_CSS entry '{path}' is not found by the static file finders.",
            hint=(
                "Put the file in the static/ folder of an installed app and give "
                "its path relative to that folder, e.g. "
                "'mt_client/css/client_theme.css'."
            ),
            id="baseclasses.W001",
        )
        for path in settings.CUSTOM_CSS
        if finders.find(path) is None
    ]

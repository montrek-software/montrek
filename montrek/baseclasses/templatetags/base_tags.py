import re

from django import template
from django.conf import settings
from django.urls import reverse

from baseclasses.navigation import build_nav_structure

register = template.Library()


@register.simple_tag
def project_display_name() -> str:
    return settings.PROJECT_NAME.replace("mt_", "").replace("_", " ").title()


@register.inclusion_tag("navbar.html", takes_context=True)
def include_navbar(context):
    user = context["user"]
    navbar_apps, navbar_dropdowns = build_nav_structure(user)
    return {
        "nav_apps": navbar_apps,
        "navbar_dropdowns": navbar_dropdowns,
        "home_url": reverse(settings.NAVBAR_HOME_URL),
        "home_label": settings.NAVBAR_HOME_LABEL,
        "user": user,
    }


@register.inclusion_tag("launchpad.html", takes_context=True)
def include_launchpad(context):
    navbar_apps, navbar_dropdowns = build_nav_structure(context["user"])
    return {
        "nav_apps": navbar_apps,
        "navbar_dropdowns": navbar_dropdowns,
    }


@register.inclusion_tag("client_logo.html")
def include_client_logo():
    client_logo_path = settings.CLIENT_LOGO_PATH
    client_logo_link = settings.CLIENT_LOGO_LINK

    is_url = bool(re.match(r"^https?://", client_logo_path))
    return {
        "client_logo_path": client_logo_path,
        "is_url": is_url,
        "client_logo_link": client_logo_link,
    }


@register.inclusion_tag("test_banner.html")
def include_test_banner():
    test_tag = settings.DEBUG
    return {"test_tag": test_tag}

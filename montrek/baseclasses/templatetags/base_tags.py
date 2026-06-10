import re

from django import template
from django.conf import settings
from django.urls import reverse

from baseclasses.dataclasses.nav_bar_model import NavBarDropdownModel, NavBarModel

register = template.Library()


@register.simple_tag
def project_display_name() -> str:
    return settings.PROJECT_NAME.replace("mt_", "").replace("_", " ").title()


def build_nav_structure() -> tuple[list[NavBarModel], list[NavBarDropdownModel]]:
    navbar_apps_config = settings.NAVBAR_APPS
    navbar_rename_config = settings.NAVBAR_RENAME
    navbar_apps = []
    navbar_dropdowns = {}

    for app in navbar_apps_config:
        if not app:
            continue
        app_structure = app.split(".")
        if len(app_structure) > 1:
            repo_name = app_structure[
                -2
            ]  # Access the second-to-last element, which represents the repository name.
            app_name = app_structure[-1]
            if repo_name not in navbar_dropdowns:
                navbar_dropdowns[repo_name] = NavBarDropdownModel(
                    repo_name, force_display_name=navbar_rename_config.get(repo_name)
                )
            dropdown = navbar_dropdowns[repo_name]
            dropdown.dropdown_items.append(
                NavBarModel(
                    app_name, force_display_name=navbar_rename_config.get(app_name)
                )
            )
        else:
            navbar_apps.append(
                NavBarModel(app, force_display_name=navbar_rename_config.get(app))
            )
    return navbar_apps, list(navbar_dropdowns.values())


@register.inclusion_tag("navbar.html", takes_context=True)
def include_navbar(context):
    navbar_apps, navbar_dropdowns = build_nav_structure()
    return {
        "nav_apps": navbar_apps,
        "navbar_dropdowns": navbar_dropdowns,
        "home_url": reverse(settings.NAVBAR_HOME_URL),
        "home_label": settings.NAVBAR_HOME_LABEL,
        "user": context["user"],
    }


@register.inclusion_tag("launchpad.html")
def include_launchpad():
    navbar_apps, navbar_dropdowns = build_nav_structure()
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

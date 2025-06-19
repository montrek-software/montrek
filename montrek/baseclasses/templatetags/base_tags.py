from django import template
from django.utils.safestring import mark_safe
from django.urls import reverse
from baseclasses.views import client_logo, test_banner
from django.conf import settings
from baseclasses.dataclasses.nav_bar_model import NavBarDropdownModel, NavBarModel

register = template.Library()


@register.inclusion_tag("navbar.html")
def include_navbar():
    navbar_apps_config = settings.NAVBAR_APPS
    navbar_rename_config = settings.NAVBAR_RENAME
    navbar_apps = []
    navbar_dropdowns = {}

    for app in navbar_apps_config:
        if not app:
            continue
        app_structure = app.split(".")
        if len(app_structure) > 1:
            repo_name = app_structure[0]
            app_name = app_structure[1]
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

    return {
        "nav_apps": navbar_apps,
        "navbar_dropdowns": navbar_dropdowns.values(),
        "home_url": reverse(settings.NAVBAR_HOME_URL),
        "home_label": settings.NAVBAR_HOME_LABEL,
    }


@register.simple_tag(takes_context=True)
def include_client_logo(context):
    request = context["request"]
    response = client_logo(request)
    return mark_safe(response.content.decode("utf-8"))


@register.simple_tag(takes_context=True)
def include_test_banner(context):
    request = context["request"]
    response = test_banner(request)
    return mark_safe(response.content.decode("utf-8"))

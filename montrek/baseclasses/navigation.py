"""The navigation structure behind the navbar and the launchpad.

Both are built from ``settings.NAVBAR_APPS``, whose entries are URL names. An
entry is shown only to a user who would get past the gate of the view it routes
to - see ``baseclasses.access.can_access_url_name``. The permission is resolved
from the route rather than declared per menu entry, so the menu cannot drift
away from what the gate actually enforces.

Hiding an entry is cosmetic: the gate stays the only thing denying access, and a
hand-typed URL is still refused.
"""

from django.conf import settings

from baseclasses.access import can_access_url_name, route_for_url_name
from baseclasses.dataclasses.nav_bar_model import NavBarDropdownModel, NavBarModel


def navigation_url_names() -> list[str]:
    """The URL name of every configured navigation entry, in order.

    An entry may be dotted (``"asset_management.fund"``), in which case all but
    the last segment only group it into a dropdown; the last segment is the URL
    name.
    """
    return [app.split(".")[-1] for app in settings.NAVBAR_APPS if app]


def build_nav_structure(user) -> tuple[list[NavBarModel], list[NavBarDropdownModel]]:
    """The entries ``user`` may follow, as top level items and dropdowns.

    A dropdown is created by its first accessible item, so one whose every item
    is filtered out never appears rather than being rendered empty.
    """
    navbar_rename_config = settings.NAVBAR_RENAME
    navbar_apps: list[NavBarModel] = []
    navbar_dropdowns: dict[str, NavBarDropdownModel] = {}

    for app in settings.NAVBAR_APPS:
        if not app:
            continue
        app_structure = app.split(".")
        app_name = app_structure[-1]
        route = route_for_url_name(app_name)
        if route is None or not can_access_url_name(user, app_name):
            continue
        url, _ = route
        nav_app = NavBarModel(
            app_name,
            force_display_name=navbar_rename_config.get(app_name),
            # Carried rather than reversed again in the template: the route was
            # resolved to decide on the entry anyway, and an entry that will not
            # reverse is dropped above instead of raising NoReverseMatch while
            # the page is rendered.
            url=url,
        )
        if len(app_structure) > 1:
            # The second-to-last element, which represents the repository name.
            repo_name = app_structure[-2]
            if repo_name not in navbar_dropdowns:
                navbar_dropdowns[repo_name] = NavBarDropdownModel(
                    repo_name, force_display_name=navbar_rename_config.get(repo_name)
                )
            navbar_dropdowns[repo_name].dropdown_items.append(nav_app)
        else:
            navbar_apps.append(nav_app)
    return navbar_apps, list(navbar_dropdowns.values())

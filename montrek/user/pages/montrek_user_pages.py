from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekDetailsPage, MontrekPage
from user.repositories.montrek_user_repositories import MontrekUserRepository


class MontrekUserPage(MontrekPage):
    page_title = "MontrekUser"

    def get_tabs(self):
        return (
            TabElement(
                name="MontrekUser",
                link=reverse("montrek_user_list"),
                html_id="tab_montrek_user_list",
                active="active",
            ),
        )


class MontrekUserDetailsPage(MontrekDetailsPage):
    repository_class = MontrekUserRepository
    title_field = "hub_entity_id"

    def get_tabs(self):
        return (
            TabElement(
                name="MontrekUser",
                link=reverse("montrek_user_details", args=[self.obj.id]),
                html_id="tab_montrek_user_details",
                active="active",
            ),
        )

from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage


class SPositionPage(MontrekPage):
    page_title = "Position"

    def get_tabs(self):
        return (
            TabElement(
                name="Position",
                link=reverse("sposition_list"),
                html_id="tab_sposition_list",
                active="active",
            ),
        )

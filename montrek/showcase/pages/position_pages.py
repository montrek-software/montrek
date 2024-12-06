from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage


class PositionPage(MontrekPage):
    page_title = "Position"

    def get_tabs(self):
        return (
            TabElement(
                name="Position",
                link=reverse("position_list"),
                html_id="tab_position_list",
                active="active",
            ),
        )

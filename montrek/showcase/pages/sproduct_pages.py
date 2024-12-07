from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage


class SProductPage(MontrekPage):
    page_title = "Investment Overview"

    def get_tabs(self):
        return (
            TabElement(
                name="SProduct",
                link=reverse("showcase"),
                html_id="tab_sproduct_list",
                active="active",
            ),
            TabElement(
                name="STransaction",
                link=reverse("stransaction_list"),
                html_id="tab_stransaction_list",
                active="",
            ),
            TabElement(
                name="SPosition",
                link=reverse("sposition_list"),
                html_id="tab_sposition_list",
                active="",
            ),
        )

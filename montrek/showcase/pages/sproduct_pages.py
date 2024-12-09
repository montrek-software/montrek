from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage


class SProductPage(MontrekPage):
    page_title = "Investment Overview"

    def get_tabs(self):
        return (
            TabElement(
                name="Product",
                link=reverse("showcase"),
                html_id="tab_sproduct_list",
                active="active",
            ),
            TabElement(
                name="Asset",
                link=reverse("sasset_list"),
                html_id="tab_sasset_list",
                active="",
            ),
            TabElement(
                name="Transaction",
                link=reverse("stransaction_list"),
                html_id="tab_stransaction_list",
                active="",
            ),
            TabElement(
                name="Position",
                link=reverse("sposition_list"),
                html_id="tab_sposition_list",
                active="",
            ),
        )

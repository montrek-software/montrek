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
                html_id="tab_product_list",
                active="active",
            ),
            TabElement(
                name="STransaction",
                link=reverse("transaction_list"),
                html_id="tab_transaction_list",
                active="",
            ),
            TabElement(
                name="Position",
                link=reverse("position_list"),
                html_id="tab_position_list",
                active="",
            ),
        )

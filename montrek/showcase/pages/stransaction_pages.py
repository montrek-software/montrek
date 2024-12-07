from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage


class STransactionPage(MontrekPage):
    page_title = "STransaction"

    def get_tabs(self):
        return (
            TabElement(
                name="STransaction",
                link=reverse("stransaction_list"),
                html_id="tab_stransaction_list",
                active="active",
            ),
        )

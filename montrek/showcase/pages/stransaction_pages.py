from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage


class STransactionPage(MontrekPage):
    page_title = "Transaction"

    def get_tabs(self):
        return (
            TabElement(
                name="Transaction",
                link=reverse("stransaction_list"),
                html_id="tab_stransaction_list",
                active="active",
            ),
            TabElement(
                name="File Upload",
                link=reverse("stransaction_fu_registry_list"),
                html_id="tab_stransaction_fu_registry_list",
                active="",
            ),
        )

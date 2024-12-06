from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage


class TransactionPage(MontrekPage):
    page_title = "Transaction"

    def get_tabs(self):
        return (
            TabElement(
                name="Transaction",
                link=reverse("transaction_list"),
                html_id="tab_transaction_list",
                active="active",
            ),
        )

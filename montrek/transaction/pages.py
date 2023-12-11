from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage
from transaction.repositories.transaction_repository import TransactionRepository

class TransactionPage(MontrekPage):

    def __init__(self, request, **kwargs):
        super().__init__(request, **kwargs)
        self.obj = TransactionRepository(self.request).std_queryset().get(pk=kwargs["pk"])
        self.page_title = f"Transaction {self.obj.pk}"

    def get_tabs(self):
        view_tab = TabElement(
            name="Details",
            link=reverse(
                "transaction_details", kwargs={"pk": self.obj.pk}
            ),
            html_id="tab_details",
            actions=(),
        )
        return (view_tab,)

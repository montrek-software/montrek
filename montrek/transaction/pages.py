from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage

class TransactionPage(MontrekPage):

    def __init__(self, repository, **kwargs):
        super().__init__(repository, **kwargs)
        self.obj = self.repository.std_queryset().get(pk=kwargs["pk"])
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

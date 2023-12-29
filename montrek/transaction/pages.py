from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage
from transaction.repositories.transaction_repository import TransactionRepository
from transaction.repositories.transaction_category_repository import TransactionCategoryMapRepository

class TransactionPage(MontrekPage):
    repository = TransactionRepository({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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

class TransactionCategoryMapPage(MontrekPage):
    repository = TransactionCategoryMapRepository({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.obj = self.repository.std_queryset().get(pk=kwargs["pk"])
        self.page_title = f"Transaction Category Map Entry {self.obj.pk}"

    def get_tabs(self):
        return ()
    #    view_tab = TabElement(
    #        name="Details",
    #        link=reverse(
    #            "transaction_category_map_details", 
    #            kwargs={"pk": self.obj.pk}
    #        ),
    #        html_id="tab_details",
    #        actions=(),
    #    )
    #    return (view_tab,)

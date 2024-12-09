from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.stransaction_managers import (
    STransactionTableManager,
)
from showcase.pages.sproduct_pages import SProductPage
from showcase.forms.stransaction_forms import STransactionCreateForm


class STransactionCreateView(MontrekCreateView):
    manager_class = STransactionTableManager
    page_class = SProductPage
    tab = "tab_stransaction_list"
    form_class = STransactionCreateForm
    success_url = "stransaction_list"
    title = "Transaction Create"


class STransactionUpdateView(MontrekUpdateView):
    manager_class = STransactionTableManager
    page_class = SProductPage
    tab = "tab_stransaction_list"
    form_class = STransactionCreateForm
    success_url = "stransaction_list"
    title = "Transaction Update"


class STransactionDeleteView(MontrekDeleteView):
    manager_class = STransactionTableManager
    page_class = SProductPage
    tab = "tab_stransaction_list"
    success_url = "stransaction_list"
    title = "Transaction Delete"


class STransactionListView(MontrekListView):
    manager_class = STransactionTableManager
    page_class = SProductPage
    tab = "tab_stransaction_list"
    title = "Transaction List"

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("stransaction_create"),
            action_id="id_create_transaction",
            hover_text="Create new Transaction",
        )
        return (action_new,)

from django.http import HttpResponseRedirect
from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.transaction_managers import (
    TransactionExampleDataGenerator,
    TransactionTableManager,
)
from showcase.models.position_hub_models import PositionHub
from showcase.models.transaction_hub_models import TransactionHub
from showcase.pages.product_pages import ProductPage
from showcase.forms.transaction_forms import TransactionCreateForm


class TransactionCreateView(MontrekCreateView):
    manager_class = TransactionTableManager
    page_class = ProductPage
    tab = "tab_transaction_list"
    form_class = TransactionCreateForm
    success_url = "transaction_list"
    title = "Transaction Create"


class TransactionUpdateView(MontrekUpdateView):
    manager_class = TransactionTableManager
    page_class = ProductPage
    tab = "tab_transaction_list"
    form_class = TransactionCreateForm
    success_url = "transaction_list"
    title = "Transaction Update"


class TransactionDeleteView(MontrekDeleteView):
    manager_class = TransactionTableManager
    page_class = ProductPage
    tab = "tab_transaction_list"
    success_url = "transaction_list"
    title = "Transaction Delete"


class TransactionListView(MontrekListView):
    manager_class = TransactionTableManager
    page_class = ProductPage
    tab = "tab_transaction_list"
    title = "Transaction List"

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("transaction_create"),
            action_id="id_create_transaction",
            hover_text="Create new Transaction",
        )
        action_load_example_data = ActionElement(
            icon="upload",
            link=reverse("load_transaction_example_data"),
            action_id="id_load_transaction_example_data",
            hover_text="Load Transaction Example Data",
        )
        action_delete_all_transaction_data = ActionElement(
            icon="trash",
            link=reverse("delete_all_transaction_data"),
            action_id="id_delete_all_transaction_data",
            hover_text="Delete all Transaction data",
        )
        return (
            action_new,
            action_delete_all_transaction_data,
            action_load_example_data,
        )


def delete_all_transaction_data(request):
    TransactionHub.objects.all().delete()
    PositionHub.objects.all().delete()
    return HttpResponseRedirect(reverse("transaction_list"))


def load_transaction_example_data(request):
    session_data = {"user_id": request.user.id}
    TransactionExampleDataGenerator(session_data).load()
    return HttpResponseRedirect(reverse("transaction_list"))

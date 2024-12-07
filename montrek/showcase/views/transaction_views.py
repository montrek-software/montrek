from django.http import HttpResponseRedirect
from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.transaction_managers import (
    STransactionExampleDataGenerator,
    STransactionTableManager,
)
from showcase.models.position_hub_models import PositionHub
from showcase.models.transaction_hub_models import STransactionHub
from showcase.pages.product_pages import SProductPage
from showcase.forms.transaction_forms import STransactionCreateForm


class STransactionCreateView(MontrekCreateView):
    manager_class = STransactionTableManager
    page_class = SProductPage
    tab = "tab_transaction_list"
    form_class = STransactionCreateForm
    success_url = "transaction_list"
    title = "STransaction Create"


class STransactionUpdateView(MontrekUpdateView):
    manager_class = STransactionTableManager
    page_class = SProductPage
    tab = "tab_transaction_list"
    form_class = STransactionCreateForm
    success_url = "transaction_list"
    title = "STransaction Update"


class STransactionDeleteView(MontrekDeleteView):
    manager_class = STransactionTableManager
    page_class = SProductPage
    tab = "tab_transaction_list"
    success_url = "transaction_list"
    title = "STransaction Delete"


class STransactionListView(MontrekListView):
    manager_class = STransactionTableManager
    page_class = SProductPage
    tab = "tab_transaction_list"
    title = "STransaction List"

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("transaction_create"),
            action_id="id_create_transaction",
            hover_text="Create new STransaction",
        )
        action_load_example_data = ActionElement(
            icon="upload",
            link=reverse("load_transaction_example_data"),
            action_id="id_load_transaction_example_data",
            hover_text="Load STransaction Example Data",
        )
        action_delete_all_transaction_data = ActionElement(
            icon="trash",
            link=reverse("delete_all_transaction_data"),
            action_id="id_delete_all_transaction_data",
            hover_text="Delete all STransaction data",
        )
        return (
            action_new,
            action_delete_all_transaction_data,
            action_load_example_data,
        )


def delete_all_transaction_data(request):
    STransactionHub.objects.all().delete()
    PositionHub.objects.all().delete()
    return HttpResponseRedirect(reverse("transaction_list"))


def load_transaction_example_data(request):
    session_data = {"user_id": request.user.id}
    STransactionExampleDataGenerator(session_data).load()
    return HttpResponseRedirect(reverse("transaction_list"))

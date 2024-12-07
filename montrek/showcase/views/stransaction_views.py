from django.http import HttpResponseRedirect
from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.stransaction_managers import (
    STransactionExampleDataGenerator,
    STransactionTableManager,
)
from showcase.models.sposition_hub_models import SPositionHub
from showcase.models.stransaction_hub_models import STransactionHub
from showcase.pages.sproduct_pages import SProductPage
from showcase.forms.stransaction_forms import STransactionCreateForm


class STransactionCreateView(MontrekCreateView):
    manager_class = STransactionTableManager
    page_class = SProductPage
    tab = "tab_stransaction_list"
    form_class = STransactionCreateForm
    success_url = "stransaction_list"
    title = "STransaction Create"


class STransactionUpdateView(MontrekUpdateView):
    manager_class = STransactionTableManager
    page_class = SProductPage
    tab = "tab_stransaction_list"
    form_class = STransactionCreateForm
    success_url = "stransaction_list"
    title = "STransaction Update"


class STransactionDeleteView(MontrekDeleteView):
    manager_class = STransactionTableManager
    page_class = SProductPage
    tab = "tab_stransaction_list"
    success_url = "stransaction_list"
    title = "STransaction Delete"


class STransactionListView(MontrekListView):
    manager_class = STransactionTableManager
    page_class = SProductPage
    tab = "tab_stransaction_list"
    title = "STransaction List"

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("stransaction_create"),
            action_id="id_create_transaction",
            hover_text="Create new STransaction",
        )
        action_load_example_data = ActionElement(
            icon="upload",
            link=reverse("load_stransaction_example_data"),
            action_id="id_load_stransaction_example_data",
            hover_text="Load Example Data",
        )
        action_delete_all_stransaction_data = ActionElement(
            icon="trash",
            link=reverse("delete_all_stransaction_data"),
            action_id="id_delete_all_stransaction_data",
            hover_text="Delete all STransaction data",
        )
        return (
            action_new,
            action_delete_all_stransaction_data,
            action_load_example_data,
        )


def delete_all_stransaction_data(request):
    STransactionHub.objects.all().delete()
    SPositionHub.objects.all().delete()
    return HttpResponseRedirect(reverse("stransaction_list"))


def load_stransaction_example_data(request):
    session_data = {"user_id": request.user.id}
    STransactionExampleDataGenerator(session_data).load()
    return HttpResponseRedirect(reverse("stransaction_list"))

from django.http import HttpResponseRedirect
from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.sproduct_managers import (
    SProductExampleDataGenerator,
    SProductTableManager,
)
from showcase.models.sproduct_hub_models import SProductHub
from showcase.pages.sproduct_pages import SProductPage
from showcase.forms.sproduct_forms import SProductCreateForm


class SProductCreateView(MontrekCreateView):
    manager_class = SProductTableManager
    page_class = SProductPage
    tab = "tab_sproduct_list"
    form_class = SProductCreateForm
    success_url = "showcase"
    title = "SProduct Create"


class SProductUpdateView(MontrekUpdateView):
    manager_class = SProductTableManager
    page_class = SProductPage
    tab = "tab_sproduct_list"
    form_class = SProductCreateForm
    success_url = "showcase"
    title = "SProduct Update"


class SProductDeleteView(MontrekDeleteView):
    manager_class = SProductTableManager
    page_class = SProductPage
    tab = "tab_sproduct_list"
    success_url = "showcase"
    title = "SProduct Delete"


class SProductListView(MontrekListView):
    manager_class = SProductTableManager
    page_class = SProductPage
    tab = "tab_sproduct_list"
    title = "SProduct List"
    do_simple_file_upload = True

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("sproduct_create"),
            action_id="id_create_product",
            hover_text="Create new SProduct",
        )
        action_load_example_data = ActionElement(
            icon="upload",
            link=reverse("load_sproduct_example_data"),
            action_id="id_load_sproduct_example_data",
            hover_text="Load Example Data",
        )
        action_delete_all_sproduct_data = ActionElement(
            icon="trash",
            link=reverse("delete_all_sproduct_data"),
            action_id="id_delete_all_sproduct_data",
            hover_text="Delete all SProduct data",
        )
        return (action_new, action_delete_all_sproduct_data, action_load_example_data)


def delete_all_sproduct_data(request):
    SProductHub.objects.all().delete()
    return HttpResponseRedirect(reverse("showcase"))


def load_sproduct_example_data(request):
    session_data = {"user_id": request.user.id}
    SProductExampleDataGenerator(session_data).load()
    return HttpResponseRedirect(reverse("showcase"))

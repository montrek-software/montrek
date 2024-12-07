from django.http import HttpResponseRedirect
from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.product_managers import (
    SProductExampleDataGenerator,
    SProductTableManager,
)
from showcase.models.product_hub_models import SProductHub
from showcase.pages.product_pages import SProductPage
from showcase.forms.product_forms import SProductCreateForm


class SProductCreateView(MontrekCreateView):
    manager_class = SProductTableManager
    page_class = SProductPage
    tab = "tab_product_list"
    form_class = SProductCreateForm
    success_url = "showcase"
    title = "SProduct Create"


class SProductUpdateView(MontrekUpdateView):
    manager_class = SProductTableManager
    page_class = SProductPage
    tab = "tab_product_list"
    form_class = SProductCreateForm
    success_url = "showcase"
    title = "SProduct Update"


class SProductDeleteView(MontrekDeleteView):
    manager_class = SProductTableManager
    page_class = SProductPage
    tab = "tab_product_list"
    success_url = "showcase"
    title = "SProduct Delete"


class SProductListView(MontrekListView):
    manager_class = SProductTableManager
    page_class = SProductPage
    tab = "tab_product_list"
    title = "SProduct List"
    do_simple_file_upload = True

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("product_create"),
            action_id="id_create_product",
            hover_text="Create new SProduct",
        )
        action_load_example_data = ActionElement(
            icon="upload",
            link=reverse("load_product_example_data"),
            action_id="id_load_product_example_data",
            hover_text="Load example data",
        )
        action_delete_all_product_data = ActionElement(
            icon="trash",
            link=reverse("delete_all_product_data"),
            action_id="id_delete_all_product_data",
            hover_text="Delete all SProduct data",
        )
        return (action_new, action_delete_all_product_data, action_load_example_data)


def delete_all_product_data(request):
    SProductHub.objects.all().delete()
    return HttpResponseRedirect(reverse("showcase"))


def load_product_example_data(request):
    session_data = {"user_id": request.user.id}
    SProductExampleDataGenerator(session_data).load()
    return HttpResponseRedirect(reverse("showcase"))

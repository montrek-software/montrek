from django.http import HttpResponseRedirect
from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.product_managers import (
    ProductExampleDataGenerator,
    ProductTableManager,
)
from showcase.models.product_hub_models import ProductHub
from showcase.pages.product_pages import ProductPage
from showcase.forms.product_forms import ProductCreateForm


class ProductCreateView(MontrekCreateView):
    manager_class = ProductTableManager
    page_class = ProductPage
    tab = "tab_product_list"
    form_class = ProductCreateForm
    success_url = "showcase"
    title = "Product Create"


class ProductUpdateView(MontrekUpdateView):
    manager_class = ProductTableManager
    page_class = ProductPage
    tab = "tab_product_list"
    form_class = ProductCreateForm
    success_url = "showcase"
    title = "Product Update"


class ProductDeleteView(MontrekDeleteView):
    manager_class = ProductTableManager
    page_class = ProductPage
    tab = "tab_product_list"
    success_url = "showcase"
    title = "Product Delete"


class ProductListView(MontrekListView):
    manager_class = ProductTableManager
    page_class = ProductPage
    tab = "tab_product_list"
    title = "Product List"
    do_simple_file_upload = True

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("product_create"),
            action_id="id_create_product",
            hover_text="Create new Product",
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
            hover_text="Delete all Product data",
        )
        return (action_new, action_delete_all_product_data, action_load_example_data)


def delete_all_product_data(request):
    ProductHub.objects.all().delete()
    return HttpResponseRedirect(reverse("showcase"))


def load_product_example_data(request):
    session_data = {"user_id": request.user.id}
    ProductExampleDataGenerator(session_data).load()
    return HttpResponseRedirect(reverse("showcase"))

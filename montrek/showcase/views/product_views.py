from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.product_managers import ProductTableManager
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

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("product_create"),
            action_id="id_create_product",
            hover_text="Create new Product",
        )
        return (action_new,)

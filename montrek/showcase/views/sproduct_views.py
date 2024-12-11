from django.http import HttpResponseRedirect
from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement, BackActionElement
from baseclasses.views import MontrekDetailView, MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.sasset_managers import SAssetExampleDataGenerator
from showcase.managers.scompany_managers import SCompanyExampleDataGenerator
from showcase.managers.sproduct_managers import (
    SProductDetailsManager,
    SProductExampleDataGenerator,
    SProductTableManager,
)
from showcase.managers.stransaction_managers import STransactionExampleDataGenerator
from showcase.pages.sproduct_pages import SProductDetailsPage, SProductPage
from showcase.forms.sproduct_forms import SProductCreateForm


class SProductCreateView(MontrekCreateView):
    manager_class = SProductTableManager
    page_class = SProductPage
    tab = "tab_sproduct_list"
    form_class = SProductCreateForm
    success_url = "showcase"
    title = "Product Create"


class SProductUpdateView(MontrekUpdateView):
    manager_class = SProductTableManager
    page_class = SProductPage
    tab = "tab_sproduct_list"
    form_class = SProductCreateForm
    success_url = "showcase"
    title = "Product Update"


class SProductDeleteView(MontrekDeleteView):
    manager_class = SProductTableManager
    page_class = SProductPage
    tab = "tab_sproduct_list"
    success_url = "showcase"
    title = "Product Delete"


class SProductListView(MontrekListView):
    manager_class = SProductTableManager
    page_class = SProductPage
    tab = "tab_sproduct_list"
    title = "Product List"
    do_simple_file_upload = True

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("sproduct_create"),
            action_id="id_create_product",
            hover_text="Create new Product",
        )
        action_init_showcase_data = ActionElement(
            icon="refresh",
            link=reverse("init_showcase_data"),
            action_id="id_init_showcase_data",
            hover_text="Initialize Showcase Data",
        )
        return (action_new, action_init_showcase_data)


class SProductDetailView(MontrekDetailView):
    manager_class = SProductDetailsManager
    page_class = SProductDetailsPage
    tab = "tab_sproduct_details"
    title = "Product Details"

    @property
    def actions(self) -> tuple:
        return (
            BackActionElement(
                url_name="showcase",
            ),
        )


def init_showcase_data(request):
    session_data = {"user_id": 1}
    SProductExampleDataGenerator(session_data).load()
    SCompanyExampleDataGenerator(session_data).load()
    SAssetExampleDataGenerator(session_data).load()
    STransactionExampleDataGenerator(session_data).load()
    return HttpResponseRedirect(reverse("showcase"))

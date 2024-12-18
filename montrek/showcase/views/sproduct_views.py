from django.http import HttpResponseRedirect
from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement, BackActionElement
from baseclasses.views import MontrekDetailView, MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.initial_db_data_generator import InitialDbDataGenerator
from showcase.managers.sproduct_managers import (
    SProductDetailsManager,
    SProductTableManager,
)
from showcase.managers.stransaction_managers import (
    SProductSPositionTableManager,
    SProductSTransactionTableManager,
)
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
        action_stransaction_fu_registry = ActionElement(
            icon="inbox",
            link=reverse("stransaction_fu_registry_list"),
            action_id="id_stransaction_fu_registry_list",
            hover_text="Go to Transaction File Upload Registry",
        )
        return (action_new, action_init_showcase_data, action_stransaction_fu_registry)


class BackToProductListActionMixin:
    @property
    def actions(self) -> tuple:
        return (
            BackActionElement(
                url_name="showcase",
            ),
        )


class SProductDetailView(BackToProductListActionMixin, MontrekDetailView):
    manager_class = SProductDetailsManager
    page_class = SProductDetailsPage
    tab = "tab_sproduct_details"
    title = "Product Details"


class SProductSTransactionListView(BackToProductListActionMixin, MontrekListView):
    manager_class = SProductSTransactionTableManager
    page_class = SProductDetailsPage
    tab = "tab_sproduct_stransaction_list"
    title = "Product Transaction List"


class SProductSPositionListView(BackToProductListActionMixin, MontrekListView):
    manager_class = SProductSPositionTableManager
    page_class = SProductDetailsPage
    tab = "tab_sproduct_sposition_list"
    title = "Product Position List"


def init_showcase_data(request):
    session_data = {"user_id": 1}
    InitialDbDataGenerator(session_data).generate()
    return HttpResponseRedirect(reverse("showcase"))

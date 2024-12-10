from django.http import HttpResponseRedirect
from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.sasset_managers import SAssetExampleDataGenerator
from showcase.managers.scompany_managers import SCompanyExampleDataGenerator
from showcase.managers.sproduct_managers import (
    SProductExampleDataGenerator,
    SProductTableManager,
)
from showcase.managers.stransaction_managers import STransactionExampleDataGenerator
from showcase.models.sasset_hub_models import SAssetHub
from showcase.models.scompany_hub_models import SCompanyHub
from showcase.models.sproduct_hub_models import SProductHub
from showcase.pages.sproduct_pages import SProductPage
from showcase.forms.sproduct_forms import SProductCreateForm
from showcase.models.stransaction_hub_models import STransactionHub


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


def init_showcase_data(request):
    session_data = {"user_id": 1}
    SProductHub.objects.all().delete()
    SCompanyHub.objects.all().delete()
    SAssetHub.objects.all().delete()
    STransactionHub.objects.all().delete()
    SProductExampleDataGenerator(session_data).load()
    SCompanyExampleDataGenerator(session_data).load()
    SAssetExampleDataGenerator(session_data).load()
    STransactionExampleDataGenerator(session_data).load()
    return HttpResponseRedirect(reverse("showcase"))

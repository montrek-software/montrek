from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekDetailView, MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.sasset_managers import SAssetDetailsManager, SAssetTableManager
from showcase.pages.sasset_pages import SassetDetailsPage
from showcase.pages.sproduct_pages import SProductPage
from showcase.forms.sasset_forms import SAssetCreateForm


class SAssetCreateView(MontrekCreateView):
    manager_class = SAssetTableManager
    page_class = SProductPage
    tab = "tab_sasset_list"
    form_class = SAssetCreateForm
    success_url = "sasset_list"
    title = "Asset Create"


class SAssetUpdateView(MontrekUpdateView):
    manager_class = SAssetTableManager
    page_class = SProductPage
    tab = "tab_sasset_list"
    form_class = SAssetCreateForm
    success_url = "sasset_list"
    title = "Asset Update"


class SAssetDeleteView(MontrekDeleteView):
    manager_class = SAssetTableManager
    page_class = SProductPage
    tab = "tab_sasset_list"
    success_url = "sasset_list"
    title = "Asset Delete"


class SAssetListView(MontrekListView):
    manager_class = SAssetTableManager
    page_class = SProductPage
    tab = "tab_sasset_list"
    title = "Asset List"

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("sasset_create"),
            action_id="id_create_asset",
            hover_text="Create new Asset",
        )
        return (action_new,)


class SAssetDetailView(MontrekDetailView):
    manager_class = SAssetDetailsManager
    page_class = SassetDetailsPage
    tab = "tab_sasset_details"
    title = "Asset Details"

from django.urls import reverse
from baseclasses.dataclasses.view_classes import ActionElement
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekCreateView
from baseclasses.views import MontrekUpdateView
from baseclasses.views import MontrekDeleteView
from showcase.managers.asset_managers import SAssetTableManager
from showcase.pages.asset_pages import SAssetPage
from showcase.forms.asset_forms import SAssetCreateForm


class SAssetCreateView(MontrekCreateView):
    manager_class = SAssetTableManager
    page_class = SAssetPage
    tab = "tab_asset_list"
    form_class = SAssetCreateForm
    success_url = "asset_list"
    title = "SAsset Create"


class SAssetUpdateView(MontrekUpdateView):
    manager_class = SAssetTableManager
    page_class = SAssetPage
    tab = "tab_asset_list"
    form_class = SAssetCreateForm
    success_url = "asset_list"
    title = "SAsset Update"


class SAssetDeleteView(MontrekDeleteView):
    manager_class = SAssetTableManager
    page_class = SAssetPage
    tab = "tab_asset_list"
    success_url = "asset_list"
    title = "SAsset Delete"


class SAssetListView(MontrekListView):
    manager_class = SAssetTableManager
    page_class = SAssetPage
    tab = "tab_asset_list"
    title = "SAsset List"

    @property
    def actions(self) -> tuple:
        action_new = ActionElement(
            icon="plus",
            link=reverse("asset_create"),
            action_id="id_create_asset",
            hover_text="Create new SAsset",
        )
        return (action_new,)

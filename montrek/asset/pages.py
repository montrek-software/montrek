from django.urls import reverse
from asset.repositories.asset_repository import AssetRepository
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage


class AssetOverviewPage(MontrekPage):
    page_title = "Assets"
    show_date_range_selector = True

    def get_tabs(self):
        action_new_asset = ActionElement(
            icon="plus",
            link=reverse("asset_create"),
            action_id="id_create_asset",
            hover_text="Create Asset",
        )
        overview_tab = TabElement(
            name="Asset List",
            link=reverse("asset"),
            html_id="tab_asset_list",
            active="active",
            actions=(action_new_asset,),
        )
        return (overview_tab,)


class AssetPage(MontrekPage):
    show_date_range_selector = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if "pk" not in kwargs:
            raise ValueError("AssetPage needs pk specified in url!")
        self.obj = AssetRepository().std_queryset().get(pk=kwargs["pk"])
        self.page_title = self.obj.asset_name

    def get_tabs(self):
        action_back = ActionElement(
            icon="arrow-left",
            link=reverse("asset"),
            action_id="back_to_overview",
            hover_text="Back to Overview",
        )
        action_update_asset = ActionElement(
            icon="pencil",
            link=reverse("asset_update", kwargs={"pk": self.obj.id}),
            action_id="id_update_asset",
            hover_text="Update Asset",
        )
        details_tab = TabElement(
            name="Details",
            link=reverse("asset_details", args=[self.obj.id]),
            html_id="tab_details",
            actions=(action_back, action_update_asset),
        )
        prices_tab = TabElement(
            name="Prices",
            link=reverse("asset_price_ts_table", args=[self.obj.id]),
            html_id="tab_asset_price_list",
            actions=(action_back,),
        )
        return [details_tab, prices_tab]

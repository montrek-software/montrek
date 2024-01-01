from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage

class AssetOverviewPage(MontrekPage):
    page_title = "Assets"

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
            actions=(action_new_asset, ),
        )
        return (overview_tab,)

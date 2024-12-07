from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage


class SAssetPage(MontrekPage):
    page_title = "SAsset"

    def get_tabs(self):
        return (
            TabElement(
                name="SAsset",
                link=reverse("asset_list"),
                html_id="tab_asset_list",
                active="active",
            ),
        )

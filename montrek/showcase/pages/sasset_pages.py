from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekPage


class SAssetPage(MontrekPage):
    page_title = "Asset"

    def get_tabs(self):
        return (
            TabElement(
                name="Asset",
                link=reverse("sasset_list"),
                html_id="tab_sasset_list",
                active="active",
            ),
        )

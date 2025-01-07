from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement
from baseclasses.pages import MontrekDetailsPage, MontrekPage
from showcase.repositories.sasset_repositories import SAssetRepository


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


class SAssetDetailsPage(MontrekDetailsPage):
    repository_class = SAssetRepository
    title_field = "asset_name"

    def get_tabs(self):
        return (
            TabElement(
                name="Asset",
                link=reverse("sasset_details", args=[self.obj.id]),
                html_id="tab_sasset_details",
            ),
        )

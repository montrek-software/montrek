from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage

class AssetOverviewPage(MontrekPage):
    def get_tabs(self):
        #action_new_account = ActionElement(
        #    icon="plus",
        #    link=reverse("account_create"),
        #    action_id="id_create_account",
        #    hover_text="Create Account",
        #)
        overview_tab = TabElement(
            name="Asset List",
            link=reverse("asset"),
            html_id="tab_asset_list",
            active="active",
            actions=(),
        )
        return (overview_tab,)

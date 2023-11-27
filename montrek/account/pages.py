from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage


class AccountOverviewPage(MontrekPage):
    page_title = "Accounts"

    def get_tabs(self):
        action_new_account = ActionElement(
            icon="plus",
            link=reverse('account_new_form'),
            action_id="id_new_account",
            hover_text="Add new Account",
        )
        overview_tab = TabElement(
            name = "Account List",
            link = reverse('account'),
            html_id="tab_account_list",
            active="active",
            actions=(action_new_account,),
        )
        return (overview_tab,)

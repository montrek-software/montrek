from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage

action_new_account = ActionElement(
    icon="plus",
    #link=reverse('account_new_form'),
    link="",
    action_id="id_new_account",
    hover_text="Add new Account",
)
overview_tab = TabElement(
    name = "Account List",
    #link = reverse('account'),
    link="",
    html_id="tab_account_list",
    active="active",
    actions=(action_new_account,),
)

class AccountOverviewPage(MontrekPage):
    page_title = "Accounts"

    @property
    def tabs(self):
        return (overview_tab,)

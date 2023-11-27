from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage

action_create = ActionElement(
    icon="plus",
    #link=reverse("credit_institution_create"),
    link="",
    action_id="create_credit_institution",
    hover_text="Create Credit Institution",
)

overview_tab = TabElement(
    name="Overview",
    #link=reverse("account"),
    link="",
    html_id="tab_overview",
    actions=(action_create,),
)


class CreditInstitutionAppPage(MontrekPage):
    @property
    def tabs(self):
        return [overview_tab]

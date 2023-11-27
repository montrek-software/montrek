from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement

action_create = ActionElement(
    icon="plus",
    link=reverse("credit_institution_create"),
    action_id="create_credit_institution",
    hover_text="Create Credit Institution",
)

overview_tab = TabElement(
    name="Overview",
    link=reverse("credit_instritution"),
    html_id="tab_overview",
    actions=(action_create),
)


class CreditInstitutionAppPage:
    @property
    def tabs(self):
        return [overview_tab]

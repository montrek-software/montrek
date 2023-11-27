from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage
from credit_institution.models import CreditInstitutionHub
from credit_institution.repositories.credit_institution_repository import (
    CreditInstitutionRepository,
)


class CreditInstitutionAppPage(MontrekPage):
    page_title = "Credit Institutions"

    def get_tabs(self):
        action_create = ActionElement(
            icon="plus",
            link=reverse("credit_institution"),
            action_id="create_credit_institution",
            hover_text="Create Credit Institution",
        )
        overview_tab = TabElement(
            name="Overview",
            link=reverse("credit_institution"),
            html_id="tab_overview",
            actions=(action_create,),
        )
        return (overview_tab,)


class CreditInstitutionPage(MontrekPage):
    def __init__(self, credit_instition_repository: CreditInstitutionRepository):
        super().__init__()
        self.page_title = credit_instition_repository.static_satellite.name
        self.credit_institution_hub = credit_instition_repository.hub

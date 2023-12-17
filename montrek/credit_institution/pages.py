from django.urls import reverse
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage
from credit_institution.repositories.credit_institution_repository import (
    CreditInstitutionRepository,
)


class CreditInstitutionAppPage(MontrekPage):
    page_title = "Credit Institutions"

    def get_tabs(self):
        action_create = ActionElement(
            icon="plus",
            link=reverse("credit_institution_create"),
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

    def __init__(self, repository, **kwargs):
        super().__init__(repository, **kwargs)
        if 'pk' not in kwargs:
            raise ValueError("AccountPage needs pk specified in url!")
        self.obj = self.repository.std_queryset().get(pk=kwargs['pk'])
        self.page_title = self.obj.credit_institution_name

    def get_tabs(self):
        action_back = ActionElement(
            icon="arrow-left",
            link=reverse("credit_institution"),
            action_id="back_to_overview",
            hover_text="Back to Overview",
        )
        view_tab = TabElement(
            name="Details",
            link=reverse(
                "credit_institution_details", args=[self.obj.id]
            ),
            html_id="tab_details",
            actions=(action_back,),
        )
        return (view_tab,)

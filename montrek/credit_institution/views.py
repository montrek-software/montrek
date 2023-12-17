from baseclasses.views import MontrekListView, MontrekDetailView, MontrekCreateView
from baseclasses.dataclasses.table_elements import StringTableElement, LinkTableElement
from credit_institution.models import CreditInstitutionStaticSatellite
from credit_institution.pages import CreditInstitutionAppPage, CreditInstitutionPage
from credit_institution.repositories.credit_institution_repository import (
    CreditInstitutionRepository,
)
from credit_institution.forms import CreditInstitutionCreateForm

# Create your views here.


class CreditInstitutionOverview(MontrekListView):
    page_class = CreditInstitutionAppPage
    tab = "tab_overview"
    title = "Overview Table"
    repository = CreditInstitutionRepository

    @property
    def elements(self) -> dict:
        return (
            StringTableElement(name="Name", attr="credit_institution_name"),
            LinkTableElement(
                name="Link",
                url="credit_institution_details",
                kwargs={"pk": "id"},
                icon="chevron-right",
                hover_text="Goto Credit Institution",
            ),
            StringTableElement(name="BIC", attr="credit_institution_bic"),
            StringTableElement(name="Upload Method", attr="account_upload_method"),
        )


class CreditInstitutionCreate(MontrekCreateView):
    page_class = CreditInstitutionAppPage
    repository = CreditInstitutionRepository
    form_classes = [CreditInstitutionCreateForm]
    success_url = "credit_institution"


class CreditIntitutionDetailView(MontrekDetailView):
    page_class = CreditInstitutionPage
    tab = "tab_details"
    repository = CreditInstitutionRepository
    title = "Details"

    @property
    def elements(self) -> dict:
        return (
            StringTableElement(name="Name", attr="credit_institution_name"),
            StringTableElement(name="BIC", attr="credit_institution_bic"),
            StringTableElement(name="Upload Method", attr="account_upload_method"),
        )

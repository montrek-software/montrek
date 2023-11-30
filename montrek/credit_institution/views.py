from baseclasses.views import MontrekListView, MontrekDetailView
from baseclasses.dataclasses.table_elements import StringTableElement, LinkTableElement
from credit_institution.models import CreditInstitutionStaticSatellite
from credit_institution.pages import CreditInstitutionAppPage, CreditInstitutionPage
from credit_institution.repositories.credit_institution_repository import (
    CreditInstitutionRepository,
)

# Create your views here.


class CreditInstitutionOverview(MontrekListView):
    #TODO: Use repository
    model = CreditInstitutionStaticSatellite
    page = CreditInstitutionAppPage()
    tab = "tab_overview"
    title = "Overview Table"

    @property
    def table_elements(self) -> dict:
        return (
            StringTableElement(name="Name", attr="credit_institution_name"),
            LinkTableElement(
                name="Link",
                url="credit_institution_details",
                kwargs={"pk": "id"},
                icon="chevron-right",
                hover_text="Goto Account",
            ),
            StringTableElement(name="BIC", attr="credit_institution_bic"),
            StringTableElement(name="Upload Method", attr="account_upload_method"),
        )


class CreditIntitutionDetailView(MontrekDetailView):
    page_class = CreditInstitutionPage
    tab = "tab_details"
    repository = CreditInstitutionRepository

    @property
    def detail_elements(self) -> dict:
        return (
            StringTableElement(name="Name", attr="credit_institution_name"),
            StringTableElement(name="BIC", attr="credit_institution_bic"),
            StringTableElement(name="Upload Method", attr="account_upload_method"),
        )

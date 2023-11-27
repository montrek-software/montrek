from baseclasses.views import MontrekListView, MontrekDetailView
from baseclasses.dataclasses.table_elements import StringTableElement
from credit_institution.models import CreditInstitutionStaticSatellite
from credit_institution.models import CreditInstitutionHub
from credit_institution.pages import CreditInstitutionAppPage, CreditInstitutionPage 

# Create your views here.


class CreditInstitutionOverview(MontrekListView):
    model = CreditInstitutionStaticSatellite
    page = CreditInstitutionAppPage()
    tab = "tab_overview"
    title = "Overview Table"

    @property
    def table_elements(self) -> dict:
        return (
            StringTableElement(name='Name', attr='credit_institution_name'),
            StringTableElement(name='BIC', attr='credit_institution_bic'),
            StringTableElement(name='Upload Method', attr= 'account_upload_method'),
        )

class CreditIntitutionDetailView(MontrekDetailView):
    model = CreditInstitutionHub
    page_class = CreditInstitutionPage
    tab = "tab_details"
    title = "Credit Institution Details"


    @property
    def detail_elements(self) -> dict:
        return (
            StringTableElement(name='Name', attr='credit_institution_name'),
            StringTableElement(name='BIC', attr='credit_institution_bic'),
            StringTableElement(name='Upload Method', attr= 'account_upload_method'),
        )

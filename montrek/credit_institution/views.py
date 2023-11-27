from django.shortcuts import render

from baseclasses.views import MontrekListView
from baseclasses.dataclasses.view_classes import TableElement
from credit_institution.models import CreditInstitutionStaticSatellite
from credit_institution.pages import CreditInstitutionAppPage

# Create your views here.


class CreditInstitutionOverview(MontrekListView):
    model = CreditInstitutionStaticSatellite
    page = CreditInstitutionAppPage()
    tab = "tab_overview"
    title = "Overview Table"

    @property
    def table_elements(self) -> dict:
        return (
            TableElement(name='Name', attr='credit_institution_name'),
            TableElement(name='BIC', attr='credit_institution_bic'),
            TableElement(name='Upload Method', attr= 'account_upload_method'),
        )

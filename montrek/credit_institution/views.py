from django.shortcuts import render

from baseclasses.views import MontrekListView
from credit_institution.models import CreditInstitutionStaticSatellite
from credit_institution.pages import CreditInstitutionAppPage

# Create your views here.


class CreditInstitutionOverview(MontrekListView):
    model = CreditInstitutionStaticSatellite
    page = CreditInstitutionAppPage()
    tab = "tab_overview"
    title = "Overview Table"

    @property
    def table_map_fields(self) -> dict:
        return {
            'Name' : {'attr': 'credit_institution_name'},
            'BIC' : {'attr': 'credit_institution_bic'},
            'Upload Method': {'attr': 'account_upload_method'},
        }

from django.shortcuts import render

from django.views.generic.list import ListView
from credit_institution.models import CreditInstitutionStaticSatellite
from credit_institution.pages import CreditInstitutionAppPage

# Create your views here.


class CreditInstitutionOverview(ListView):
    model = CreditInstitutionStaticSatellite
    template_name = "base.html"
    page = CreditInstitutionAppPage()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tab_elements"] = self.page.tabs
        return context

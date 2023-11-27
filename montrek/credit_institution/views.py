from django.shortcuts import render

from django.views.generic.list import ListView
from credit_institution.models import CreditInstitutionStaticSatellite
# Create your views here.

class CreditInstitutionOverview(ListView):
    model = CreditInstitutionStaticSatellite
    template_name = 'base.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

from django.shortcuts import render

from baseclasses.views import MontrekCreateView
from country.pages import CountryOverviewPage
from country.repositories.country_repository import CountryRepository
from country.forms import CountryCreateForm


# Create your views here.
class CountryCreateView(MontrekCreateView):
    page_class = CountryOverviewPage
    repository = CountryRepository
    title = "Country"
    form_class = CountryCreateForm
    success_url = "home"

from django.shortcuts import render

from baseclasses.views import MontrekCreateView, MontrekListView, MontrekDetailView, MontrekUpdateView
from baseclasses.dataclasses import table_elements
from country.pages import CountryOverviewPage, CountryPage
from country.repositories.country_repository import CountryRepository
from country.forms import CountryCreateForm


class CountryCreateView(MontrekCreateView):
    page_class = CountryOverviewPage
    repository = CountryRepository
    title = "Country"
    form_class = CountryCreateForm
    success_url = "country"


class CountryOverview(MontrekListView):
    page_class = CountryOverviewPage
    tab = "tab_country_list"
    title = "Country Overview"
    repository = CountryRepository

    @property
    def elements(self) -> tuple:
        return (
            table_elements.StringTableElement(
                name="Country Name",
                attr="country_name",
            ),
            table_elements.StringTableElement(
                name="Country Code",
                attr="country_code",
            ),
        )

class CountryDetailsView(MontrekDetailView):
    page_class = CountryPage
    repository = CountryRepository
    tab = "tab_details"
    title = "Country Details"

    @property
    def elements(self) -> tuple:
        return (
            table_elements.StringTableElement(
                name="Country Name",
                attr="country_name",
            ),
            table_elements.StringTableElement(
                name="Country Code",
                attr="country_code",
            ),
        )

class CountryUpdateView(MontrekUpdateView):
    page_class = CountryPage
    repository = CountryRepository
    title = "Country Update"
    form_class = CountryCreateForm
    success_url = "country"

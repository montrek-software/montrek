from django.shortcuts import render

from baseclasses.views import (
    MontrekCreateView,
    MontrekListView,
    MontrekDetailView,
    MontrekUpdateView,
)
from baseclasses.dataclasses import table_elements
from company.pages import CompanyOverviewPage, CompanyPage
from company.repositories.company_repository import CompanyRepository
from company.forms import CompanyCreateForm


class CompanyCreateView(MontrekCreateView):
    page_class = CompanyOverviewPage
    repository = CompanyRepository
    title = "Company"
    form_class = CompanyCreateForm
    success_url = "company"


class CompanyOverview(MontrekListView):
    page_class = CompanyOverviewPage
    tab = "tab_company_list"
    title = "Company Overview"
    repository = CompanyRepository

    @property
    def elements(self) -> tuple:
        return (
            table_elements.StringTableElement(
                name="Company Name",
                attr="company_name",
            ),
            table_elements.StringTableElement(
                name="Bloomberg Ticker",
                attr="bloomberg_ticker",
            ),
        )


class CompanyDetailsView(MontrekDetailView):
    page_class = CompanyPage
    repository = CompanyRepository
    tab = "tab_details"
    title = "Company Details"

    @property
    def elements(self) -> tuple:
        return (
            table_elements.StringTableElement(
                name="Company Name",
                attr="company_name",
            ),
            table_elements.StringTableElement(
                name="Bloomberg Ticker",
                attr="bloomberg_ticker",
            ),
        )


class CompanyUpdateView(MontrekUpdateView):
    page_class = CompanyPage
    repository = CompanyRepository
    title = "Company Update"
    form_class = CompanyCreateForm
    success_url = "company"

from baseclasses.views import (
    MontrekCreateView,
    MontrekDeleteView,
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
            table_elements.LinkTableElement(
                name="View",
                url="company_details",
                kwargs={"pk": "id"},
                icon="eye-open",
                hover_text="View Company",
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


class CompanyDeleteView(MontrekDeleteView):
    repository = CompanyRepository
    page_class = CompanyOverviewPage
    success_url = "company"


class CompanyTSTableView(MontrekListView):
    page_class = CompanyPage
    tab = "tab_company_ts_table"
    title = "Company Time Series"
    repository = CompanyRepository

    def get_queryset(self):
        company_id = self.kwargs["pk"]
        return self.repository_object.get_all_time_series(company_id)

    @property
    def elements(self) -> tuple:
        return (
            table_elements.DateTableElement(
                name="Value Date",
                attr="value_date",
            ),
            table_elements.FloatTableElement(
                name="Total Revenue",
                attr="total_revenue",
            ),
        )

from django.urls import reverse

from baseclasses.views import (
    MontrekCreateView,
    MontrekDeleteView,
    MontrekHistoryListView,
    MontrekListView,
    MontrekDetailView,
    MontrekUpdateView,
)
from baseclasses.dataclasses import table_elements
from baseclasses.dataclasses.number_shortener import BillionShortening
from company.pages import CompanyOverviewPage, CompanyPage
from company.repositories.company_repository import CompanyRepository
from company.forms import CompanyCreateForm
from file_upload.views import MontrekUploadFileView
from company.managers.company_file_upload_manager import CompanyFileUploadProcessor


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

    def get_queryset(self):
        return self.repository_object.get_company_table_paginated()

    @property
    def elements(self) -> tuple:
        return (
            table_elements.StringTableElement(
                name="Effectual Company Identifier",
                attr="effectual_company_id",
            ),
            table_elements.StringTableElement(
                name="Company Name",
                attr="company_name",
            ),
            table_elements.StringTableElement(
                name="Bloomberg Ticker",
                attr="bloomberg_ticker",
            ),
            table_elements.StringTableElement(
                name="Share Class FIGI",
                attr="share_class_figi",
            ),
            table_elements.DollarTableElement(
                name="Total Revenue",
                attr="total_revenue",
                shortener=BillionShortening(),
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
                name="Effectual Company Identifier",
                attr="effectual_company_id",
            ),
            table_elements.StringTableElement(
                name="Company Name",
                attr="company_name",
            ),
            table_elements.StringTableElement(
                name="Bloomberg Ticker",
                attr="bloomberg_ticker",
            ),
            table_elements.StringTableElement(
                name="Share Class FIGI",
                attr="share_class_figi",
            ),
            table_elements.DollarTableElement(
                name="Total Revenue",
                attr="total_revenue",
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
            table_elements.DollarTableElement(
                name="Total Revenue",
                attr="total_revenue",
            ),
        )


class CompanyUploadFileView(MontrekUploadFileView):
    page_class = CompanyOverviewPage
    title = "Upload Company File"
    repository = CompanyRepository
    file_upload_processor_class = CompanyFileUploadProcessor
    accept = ".xlsx"

    def get_success_url(self):
        return reverse("company_view_uploads")


class CompanyUploadView(MontrekListView):
    page_class = CompanyOverviewPage
    tab = "tab_uploads"
    title = "Company Uploads"
    repository = CompanyRepository

    def get_queryset(self):
        return self.repository().get_upload_registry_table_paginated()

    @property
    def elements(self) -> list:
        return (
            table_elements.StringTableElement(name="File Name", attr="file_name"),
            table_elements.StringTableElement(
                name="Upload Status", attr="upload_status"
            ),
            table_elements.StringTableElement(
                name="Upload Message", attr="upload_message"
            ),
            table_elements.DateTableElement(name="Upload Date", attr="created_at"),
            table_elements.LinkTableElement(
                name="File",
                url="montrek_download_file",
                kwargs={"pk": "id"},
                icon="download",
                hover_text="Download",
            ),
        )


class CompanyHistoryView(MontrekHistoryListView):
    repository = CompanyRepository
    page_class = CompanyPage
    tab = "tab_history"
    title = "Company History"

    @property
    def elements(self) -> tuple:
        return (
            table_elements.StringTableElement(
                name="Effectual Company Identifier",
                attr="effectual_company_id",
            ),
            table_elements.StringTableElement(
                name="Company Name",
                attr="company_name",
            ),
            table_elements.StringTableElement(
                name="Bloomberg Ticker",
                attr="bloomberg_ticker",
            ),
            table_elements.StringTableElement(
                name="Share Class FIGI",
                attr="share_class_figi",
            ),
            table_elements.DateTableElement(
                name="Value Date",
                attr="value_date",
            ),
            table_elements.DollarTableElement(
                name="Total Revenue",
                attr="total_revenue",
            ),
            table_elements.DateTableElement(name="Change Date", attr="change_date"),
            table_elements.StringTableElement(name="Changed By", attr="changed_by"),
        )

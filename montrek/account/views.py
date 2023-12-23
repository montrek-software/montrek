from datetime import timedelta
from typing import Tuple
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django_pandas.io import read_frame

from account.models import AccountHub
from account.models import AccountStaticSatellite
from account.models import BankAccountPropertySatellite
from account.models import BankAccountStaticSatellite
from account.repositories.account_model_queries import new_account
from account.repositories.account_repository import AccountRepository
from account.pages import AccountOverviewPage
from account.pages import AccountPage


from credit_institution.models import CreditInstitutionStaticSatellite

from baseclasses.repositories.db_helper import new_satellite_entry
from baseclasses.forms import DateRangeForm
from baseclasses.views import MontrekListView
from baseclasses.views import MontrekDetailView
from baseclasses.views import MontrekTemplateView
from baseclasses.dataclasses.table_elements import StringTableElement
from baseclasses.dataclasses.table_elements import LinkTableElement
from baseclasses.dataclasses.table_elements import LinkTextTableElement
from baseclasses.dataclasses.table_elements import EuroTableElement
from baseclasses.dataclasses.table_elements import DateTableElement
from baseclasses.dataclasses.table_elements import BooleanTableElement
from baseclasses.dataclasses.table_elements import FloatTableElement
from baseclasses.dataclasses.table_elements import PercentTableElement

from reporting.managers.account_transaction_plots import (
    draw_monthly_income_expanses_plot,
    draw_income_expenses_category_pie_plot,
)


# Create your views here.
#### Account Views ####
def account_new(request):
    account_type = request.POST.get("account_type", "Other")
    account_name = request.POST["account_name"]
    if account_type == "Other":
        new_account(request.POST["account_name"])
        return redirect("/account/list")
    if account_type in ["Bank Account", "Depot"]:
        return redirect(
            reverse(
                "bank_account_new_form",
                kwargs={"account_name": account_name, "account_type": account_type},
            )
        )
    return render(request, "under_construction.html")


def account_new_form(request):
    account_types = AccountStaticSatellite.AccountType.choices
    return render(request, "new_account_form.html", {"account_types": account_types})


class AccountOverview(MontrekListView):
    page_class = AccountOverviewPage
    tab = "tab_account_list"
    title = "Overview Table"
    repository = AccountRepository

    @property
    def elements(self) -> list:
        return (
            StringTableElement(name="Name", attr="account_name"),
            LinkTableElement(
                name="Link",
                url="account_details",
                kwargs={"pk": "id"},
                icon="chevron-right",
                hover_text="Goto Account",
            ),
            EuroTableElement(
                name="Value",
                attr="account_value",
            ),
            StringTableElement(name="Type", attr="account_type"),
        )


class AccountDetailView(MontrekDetailView):
    page_class = AccountPage
    tab = "tab_details"
    repository = AccountRepository
    title = "Account Details"

    @property
    def elements(self) -> list:
        return (
            StringTableElement(name="Name", attr="account_name"),
            StringTableElement(name="Type", attr="account_type"),
            StringTableElement(
                name="Iban",
                attr="bank_account_iban",
            ),
            EuroTableElement(
                name="Value",
                attr="account_value",
            ),
            StringTableElement(
                name="Credit Institution",
                attr="credit_institution_name",
            ),
            StringTableElement(
                name="BIC",
                attr="credit_institution_bic",
            ),
        )


def account_delete(request, account_id: int):
    account_statics = AccountStaticSatellite.objects.get(hub_entity=account_id)
    account_statics.delete()
    account = AccountHub.objects.get(id=account_id)
    account.delete()
    return redirect("/account/list")


def account_delete_form(request, account_id: int):
    account_statics = AccountStaticSatellite.objects.get(hub_entity=account_id)
    return render(
        request, "account_delete_form.html", {"account_statics": account_statics}
    )


#### Bank Account Views ####


def bank_account_new_form(request, account_name: str, account_type: str):
    return render(
        request,
        "bank_account_new_form.html",
        {
            "credit_institutions": CreditInstitutionStaticSatellite.objects.all(),
            "account_name": account_name,
            "account_type": account_type,
        },
    )


def bank_account_new(request, account_name: str, account_type: str):
    account_hub = new_account(account_name, account_type.replace(" ", ""))
    BankAccountPropertySatellite.objects.create(
        hub_entity=account_hub,
    )
    new_satellite_entry(
        hub_entity=account_hub,
        satellite_class=BankAccountStaticSatellite,
        bank_account_iban=request.POST["bank_account_iban"],
    )
    credit_institution_name = request.POST["credit_institution_name"]
    return redirect("/account/list")


class AccountTransactionsView(MontrekListView):
    page_class = AccountPage
    tab = "tab_transactions"
    title = "Account Transactions"
    repository = AccountRepository

    def get_queryset(self):
        return self.repository_object.get_transaction_table_by_account_paginated(
            self.kwargs["pk"]
        )

    @property
    def elements(self) -> list:
        return (
            StringTableElement(name="Counterparty", attr="transaction_party"),
            LinkTableElement(
                name="CP Cat",
                url="transaction_category_add_form_with_counterparty",
                kwargs={
                    "account_id": str(self.kwargs["pk"]),
                    "counterparty": "transaction_party",
                },
                icon="tag",
                hover_text="Set Category based on Counterparty",
            ),
            StringTableElement(name="IBAN", attr="transaction_party_iban"),
            LinkTableElement(
                name="IBAN Cat",
                url="transaction_category_add_form_with_iban",
                kwargs={
                    "account_id": str(self.kwargs["pk"]),
                    "iban": "transaction_party_iban",
                },
                icon="tag",
                hover_text="Set Category based on IBAN",
            ),
            StringTableElement(name="Description", attr="transaction_description"),
            DateTableElement(name="Date", attr="transaction_date"),
            EuroTableElement(name="Value", attr="transaction_value"),
            StringTableElement(name="Category", attr="transaction_category"),
            LinkTableElement(
                name="View",
                url="transaction_details",
                kwargs={"pk": "id"},
                icon="eye-open",
                hover_text="View",
            ),
        )


class AccountGraphsView(MontrekTemplateView):
    page_class = AccountPage
    tab = "tab_graphs"
    title = "Account Graphs"
    repository = AccountRepository
    template_name = "account_graphs.html"

    def get_queryset(self):
        return self.repository_object.get_transaction_table_by_account(
            self.kwargs["pk"]
        )

    def get_template_context(self) -> dict:
        account_transactions = self.get_queryset().all()
        account_transactions_df = read_frame(account_transactions)
        account_data = {}
        income_expanse_plot = draw_monthly_income_expanses_plot(
            account_transactions_df
        ).format_html()
        account_data["income_expanse_plot"] = income_expanse_plot
        category_pie_plots = draw_income_expenses_category_pie_plot(
            account_transactions
        )
        account_data["income_category_pie_plot"] = category_pie_plots[
            "income"
        ].format_html()
        account_data["expense_category_pie_plot"] = category_pie_plots[
            "expense"
        ].format_html()
        return account_data


class AccountUploadView(MontrekListView):
    page_class = AccountPage
    tab = "tab_uploads"
    title = "Account Uploads"
    repository = AccountRepository

    def get_queryset(self):
        return self.repository_object.get_upload_registry_table_by_account_paginated(
            self.kwargs["pk"]
        )

    @property
    def elements(self) -> list:
        return (
            StringTableElement(name="File Name", attr="file_name"),
            StringTableElement(name="Upload Status", attr="upload_status"),
            StringTableElement(name="Upload Message", attr="upload_message"),
            DateTableElement(name="Upload Date", attr="created_at"),
            LinkTableElement(
                name="File",
                url="download_upload_file",
                kwargs={"upload_registry_id": "id"},
                icon="download",
                hover_text="Download",
            ),
        )


class AccountTransactionCategoryMapView(MontrekListView):
    page_class = AccountPage
    tab = "tab_transaction_category_map"
    title = "Transaction Category Map"
    repository = AccountRepository

    def get_queryset(self):
        return self.repository_object.get_transaction_category_map_table_by_account_paginated(
            self.kwargs["pk"]
        )

    @property
    def elements(self) -> list:
        return (
            StringTableElement(name="Field", attr="field"),
            StringTableElement(name="Value", attr="value"),
            StringTableElement(name="Category", attr="category"),
            BooleanTableElement(name="Is Regex", attr="is_regex"),
            LinkTableElement(
                name="Edit",
                url="transaction_category_map_edit",
                kwargs={"pk": "id", "account_id": str(self.kwargs["pk"])},
                icon="edit",
                hover_text="Edit",
            ),
            LinkTableElement(
                name="Delete",
                url="transaction_category_map_delete",
                kwargs={"pk": "id", "account_id": str(self.kwargs["pk"])},
                icon="trash",
                hover_text="Delete",
            ),
        )


class AccountDepotView(MontrekListView):
    page_class = AccountPage
    tab = "tab_depot"
    title = "Depot"
    repository = AccountRepository

    def get_queryset(self):
        return self.repository_object.get_depot_stats_table_by_account_paginated(self.kwargs["pk"])

    def elements(self) -> list:
        return (
            StringTableElement(name="Asset Name", attr="asset_name"),
            StringTableElement(name="Type", attr="asset_type"),
            StringTableElement(name="ISIN", attr="asset_isin"),
            StringTableElement(name="WKN", attr="asset_wkn"),
            LinkTextTableElement(
                name="CCY",
                url="currency_details",
                kwargs={"pk": "ccy_id"},
                text="ccy_code",
                hover_text="View Currency",
            ),
            StringTableElement(name="CCY", attr="ccy_code"),
            FloatTableElement(name="Nominal", attr="total_nominal"),
            FloatTableElement(name="FX-Rate", attr="fx_rate"),
            FloatTableElement(name="Book Price", attr="book_price"),
            EuroTableElement(name="Book Value", attr="book_value"),
            FloatTableElement(name="Current Price", attr="price"),
            EuroTableElement(name="Current Value", attr="value"),
            EuroTableElement(name="PnL", attr="profit_loss"),
            PercentTableElement(name="Performance", attr="performance"),
            DateTableElement(name="Value Date", attr="value_date"),
            LinkTableElement(
                name="",
                url="add_single_price_to_asset",
                kwargs={"account_id": str(self.kwargs["pk"]), "asset_id": "id"},
                icon="plus",
                hover_text="Add Price",
            ),
        )

from dataclasses import dataclass
from typing import Dict

from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django_pandas.io import read_frame

from account.models import AccountHub
from account.models import AccountStaticSatellite
from account.models import BankAccountPropertySatellite
from account.models import BankAccountStaticSatellite
from account.repositories.account_model_queries import new_account
from account.repositories.account_model_queries import account_view_data

from transaction.repositories.transaction_account_queries import (
    get_transactions_by_account_id,
)
from transaction.repositories.transaction_account_queries import get_paginated_transactions

from file_upload.repositories.upload_registry_account_queries import get_paginated_upload_registries

from credit_institution.repositories.credit_institution_model_queries import (
    get_credit_institution_satellite_by_account_hub_id,
)
from credit_institution.repositories.credit_institution_model_queries import (
    new_credit_institution_to_account,
)
from credit_institution.models import CreditInstitutionStaticSatellite

from baseclasses.repositories.db_helper import new_satellite_entry

from reporting.managers.account_transaction_plots import (
    draw_monthly_income_expanses_plot,
)
# Create your views here.
#### Account Views ####
def account_new(request):
    account_type = request.POST.get("account_type", "Other")
    account_name = request.POST["account_name"]
    if account_type == "Other":
        new_account(request.POST["account_name"])
        return redirect("/account/list")
    if account_type == "Bank Account":
        return redirect(f"/account/bank_account/new_form/{account_name}")
    return render(request, "under_construction.html")


def account_new_form(request):
    account_types = AccountStaticSatellite.AccountType.choices
    return render(request, "new_account_form.html", {"account_types": account_types})


def account_list(request):
    accounts_statics = AccountHub.objects.all().prefetch_related(
        "accountstaticsatellite_set", "bankaccountpropertysatellite_set"
    )
    return render(request, "account_list.html", {"items": accounts_statics})



def account_view(request, account_id: int):
    account_data = account_view_data(account_id)
    page_number = request.GET.get('page', 1)
    account_data['transactions_page'] = get_paginated_transactions(account_id, page_number)
    return render(request, "account_view.html", account_data)


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


def bank_account_new_form(request, account_name: str):
    return render(
        request,
        "bank_account_new_form.html",
        {
            "credit_institutions": CreditInstitutionStaticSatellite.objects.all(),
            "account_name": account_name,
        },
    )


def bank_account_new(request, account_name: str):
    account_hub = new_account(account_name, "BankAccount")
    BankAccountPropertySatellite.objects.create(
        hub_entity=account_hub,
    )
    new_satellite_entry(
        hub_entity=account_hub,
        satellite_class=BankAccountStaticSatellite,
        bank_account_iban=request.POST["bank_account_iban"],
    )
    credit_institution_name = request.POST["credit_institution_name"]
    new_credit_institution_to_account(credit_institution_name, account_hub)
    return redirect("/account/list")


def bank_account_view_data(account_id: int):
    account_data = account_view_data(account_id)
    bank_account_static_satellite = BankAccountStaticSatellite.objects.get(
        hub_entity=account_id
    )
    bank_account_property_satellite = BankAccountPropertySatellite.objects.get(
        hub_entity=account_id
    )
    account_data["bank_account_statics"] = bank_account_static_satellite
    account_data["bank_account_properties"] = bank_account_property_satellite
    account_data[
        "credit_institution"
    ] = get_credit_institution_satellite_by_account_hub_id(account_id)
    return account_data


def bank_account_view(request, account_id: int):
    return bank_account_view_overview(request, account_id)

def bank_account_view_overview(request, account_id: int):
    account_data = account_view_data(account_id)
    bank_account_static_satellite = BankAccountStaticSatellite.objects.get(
        hub_entity=account_id
    )
    bank_account_property_satellite = BankAccountPropertySatellite.objects.get(
        hub_entity=account_id
    )
    account_data["bank_account_statics"] = bank_account_static_satellite
    account_data["bank_account_properties"] = bank_account_property_satellite
    account_data[
        "credit_institution"
    ] = get_credit_institution_satellite_by_account_hub_id(account_id)
    return render(request, "bank_account_view_overview.html", account_data)

@dataclass
class MontrekDataTable:
    fields: Dict[str,str]
    table_objects: Paginator

def bank_account_view_transactions(request, account_id: int):
    account_data = account_view_data(account_id)
    # Get the paginated transactions
    page_number = request.GET.get('page', 1)
    transaction_fields = {'Description': 'transaction_description',
                          'Date': 'transaction_date',
                          'Amount': 'transaction_amount',
                          'Price': 'transaction_price',
                          'Value': 'transaction_value',
                          'Category': 'transaction_category.typename',
                         }
    data_table = MontrekDataTable(
        fields = transaction_fields,
        table_objects = get_paginated_transactions(account_id, page_number)
    )
    account_data.update({'columns': data_table.fields.keys(),
                         'items': data_table.fields.values(),
                         'table_objects': data_table.table_objects,
                        })
    return render(request, "bank_account_view_transactions.html", account_data)

def bank_account_view_graphs(request, account_id: int):
    account_data = account_view_data(account_id)
    account_transactions = (
        get_transactions_by_account_id(account_id).order_by("-transaction_date").all()
    )
    account_transactions_df = read_frame(account_transactions)
    income_expanse_plot = draw_monthly_income_expanses_plot(
        account_transactions_df
    ).format_html()
    account_data["income_expanse_plot"] = income_expanse_plot
    return render(request, "bank_account_view_graphs.html", account_data)

def bank_account_view_uploads(request, account_id: int):
    account_data = account_view_data(account_id)
    page_number = request.GET.get('page', 1)
    account_data['upload_registries_page'] = (
        get_paginated_upload_registries(account_id, page_number)
    )
    return render(request, "bank_account_view_uploads.html", account_data)

def bank_account_view_transaction_category_map(request, account_id: int):
    account_data = account_view_data(account_id)
    return render(request, "bank_account_view_transaction_category_map.html", account_data)

from datetime import datetime, timedelta
from typing import Tuple
from django.shortcuts import render, redirect
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
from transaction.repositories.transaction_account_queries import (
    get_paginated_transactions
)
from transaction.repositories.transaction_account_queries import (
    get_paginated_transactions_category_map
)

from file_upload.repositories.upload_registry_account_queries import get_paginated_upload_registries

from credit_institution.repositories.credit_institution_model_queries import (
    get_credit_institution_satellite_by_account_hub_id,
)
from credit_institution.repositories.credit_institution_model_queries import (
    new_credit_institution_to_account,
)
from credit_institution.models import CreditInstitutionStaticSatellite

from baseclasses.repositories.db_helper import new_satellite_entry
from baseclasses.forms import DateRangeForm

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
    account_data.update(_handle_date_range_form(request))
    page_number = request.GET.get('page', 1)
    start_date, end_date = _get_date_range_dates(request)
    account_data['transactions_page'] = get_paginated_transactions(
        account_id, start_date, end_date, page_number
    )
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
    account_data = account_view_data(account_id, "tab_overview")
    account_data.update(_handle_date_range_form(request))
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

def bank_account_view_transactions(request, account_id: int):
    account_data = account_view_data(account_id, "tab_transactions")
    account_data.update(_handle_date_range_form(request))
    # Get the paginated transactions
    page_number = request.GET.get('page', 1)
    transaction_fields = {
        'Counterparty': {'attr': 'transaction_party'},
        'CP Cat': {'link': {'url': 'transaction_category_add_form_with_counterparty',
                            'kwargs': {'account_id': str(account_id),
                                       'counterparty': 'transaction_party'},
                            'icon': 'tag',
                            'hover_text': 'Set Category based on Counterparty',
                           },
                  },
        'IBAN': {'attr': 'transaction_party_iban'},
        'IBAN Cat': {'link': {'url': 'transaction_category_add_form_with_iban',
                            'kwargs': {'account_id': str(account_id),
                                       'iban': 'transaction_party_iban'},
                            'icon': 'tag',
                            'hover_text': 'Set Category based on IBAN',
                           },
                  },
        'Description': {'attr': 'transaction_description'},
        'Date': {'attr': 'transaction_date'},
        'Value': {'attr': 'transaction_value'},
        'Category': {'attr': 'transaction_category.typename'},
        'View': {
            'link': {'url': 'transaction_view',
                     'kwargs': {'pk':'id'},
                     'icon': 'eye-open', 
                     'hover_text': 'View',
                   },
        },
                         }
    account_data['columns'] = transaction_fields.keys()
    account_data['items'] = transaction_fields.values()
    start_date, end_date = _get_date_range_dates(request)
    account_data['table_objects'] = get_paginated_transactions(
        account_id, start_date, end_date, page_number)
    return render(request, "bank_account_view_table.html", account_data)

def bank_account_view_graphs(request, account_id: int):
    account_data = account_view_data(account_id, "tab_graphs")
    account_data.update(_handle_date_range_form(request))
    account_transactions = (
        get_transactions_by_account_id(account_id).order_by("-transaction_date").all()
    )
    start_date, end_date = _get_date_range_dates(request)
    account_transactions = account_transactions.filter(
        transaction_date__gte=start_date, transaction_date__lte=end_date
    )
    account_transactions_df = read_frame(account_transactions)
    income_expanse_plot = draw_monthly_income_expanses_plot(
        account_transactions_df
    ).format_html()
    account_data["income_expanse_plot"] = income_expanse_plot
    income_category_pie_plot, expense_category_pie_plot = (
        draw_income_expenses_category_pie_plot(
            account_transactions
        )
    )
    account_data["income_category_pie_plot"] = income_category_pie_plot.format_html()
    account_data["expense_category_pie_plot"] = expense_category_pie_plot.format_html()
    return render(request, "bank_account_view_graphs.html", account_data)

def bank_account_view_uploads(request, account_id: int):
    account_data = account_view_data(account_id, "tab_uploads")
    account_data.update(_handle_date_range_form(request))
    page_number = request.GET.get('page', 1)
    upload_fields = {
        'File Name': {'attr': 'file_name'},
        'Upload Status': {'attr': 'upload_status'},
        'Upload Message': {'attr': 'upload_message'},
        'Upload Date': {'attr': 'created_at'},
        'File': {'link': {'url': 'download_upload_file',
                          'kwargs': {'upload_registry_id':'hub_entity.id'},
                          'icon': 'download',
                          'hover_text': 'Download',
                         }
                 }
    }
    account_data['columns'] = upload_fields.keys()
    account_data['items'] = upload_fields.values()
    account_data['table_objects'] = get_paginated_upload_registries(account_id, page_number)
    return render(request, "bank_account_view_table.html", account_data)

def bank_account_view_transaction_category_map(request, account_id: int):
    account_data = account_view_data(account_id, "tab_transaction_category_map")
    account_data.update(_handle_date_range_form(request))
    page_number = request.GET.get('page', 1)
    trans_cat_map_fields = {
        'Field' : {'attr': 'field'},
        'Value' : {'attr': 'value'},
        'Category' : {'attr': 'category'},
        'Is Regex' : {'attr': 'is_regex'},
        'Edit': {
            'link': {'url': 'transaction_category_map_edit',
                     'kwargs': {'pk':'id',
                                'account_id': str(account_id)},
                     'icon': 'edit', 
                     'hover_text': 'Edit',
                   },
        },
        'Delete': {
            'link': {'url': 'transaction_category_map_delete',
                     'kwargs': {'pk':'id',
                                'account_id': str(account_id)},
                     'icon': 'trash', 
                     'hover_text': 'Delete',
                   },
        },
    }
    account_data['columns'] = trans_cat_map_fields.keys()
    account_data['items'] = trans_cat_map_fields.values()
    account_data['table_objects'] = get_paginated_transactions_category_map(account_id, page_number)
    return render(request, "bank_account_view_table.html", account_data)


def _handle_date_range_form(request):
    start_date, end_date = _get_date_range_dates(request)
    request_get = request.GET.copy()
    request_get = request_get if 'start_date' in request_get and 'end_date' in request_get else None
    date_range_form = DateRangeForm(request_get or {'start_date': start_date, 'end_date': end_date})
    if date_range_form.is_valid():
        start_date = date_range_form.cleaned_data['start_date']
        end_date = date_range_form.cleaned_data['end_date']
        request.session['start_date'] = start_date.strftime('%Y-%m-%d')
        request.session['end_date'] = end_date.strftime('%Y-%m-%d')
    return {'date_range_form': date_range_form}

def _get_date_range_dates(request) -> Tuple[str, str]:
    today = datetime.today().date()
    default_start_date = today - timedelta(days=30)
    default_end_date = today
    default_start_date = default_start_date.strftime('%Y-%m-%d')
    default_end_date = default_end_date.strftime('%Y-%m-%d')

    try:
        start_date_str = request.session.get('start_date', default_start_date)
    except ValueError:
        start_date_str = default_start_date

    try:
        end_date_str = request.session.get('end_date', default_end_date)
    except ValueError:
        end_date_str = default_end_date

    return start_date_str, end_date_str

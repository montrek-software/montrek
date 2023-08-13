from django.apps import apps
import datetime
from typing import List
from django_pandas.io import read_frame

from baseclasses import models as baseclass_models
from baseclasses.repositories.db_helper import new_satellite_entry
from transaction.repositories.transaction_account_queries import (
    get_transactions_by_account_id,
)
from reporting.managers.account_transaction_plots import (
    draw_monthly_income_expanses_plot,
)

def account_hub():
    return apps.get_model("account", "AccountHub")


def account_static_satellite():
    return apps.get_model("account", "AccountStaticSatellite")


def credit_institution_hub():
    return apps.get_model("credit_institution", "CreditInstitutionHub")


def credit_institution_static_satellite():
    return apps.get_model("credit_institution", "CreditInstitutionStaticSatellite")


def new_account(
    account_name: str, account_type: str = "Other"
) -> baseclass_models.MontrekHubABC:
    account_hub_object = account_hub().objects.create()
    new_satellite_entry(
        hub_entity=account_hub_object,
        satellite_class=account_static_satellite(),
        account_type=account_type,
        account_name=account_name,
    )
    return account_hub_object


def account_view_data(account_id: int):
    account_statics = account_static_satellite().objects.get(hub_entity=account_id)
    account_transactions = (
        get_transactions_by_account_id(account_id).order_by("-transaction_date").all()
    )
    account_transactions_df = read_frame(account_transactions)
    income_expanse_plot = draw_monthly_income_expanses_plot(
        account_transactions_df
    ).format_html()
    return {
        "account_statics": account_statics,
        "account_transactions": account_transactions,
        "income_expanse_plot": income_expanse_plot,
    }

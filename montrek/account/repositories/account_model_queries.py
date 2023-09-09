from django.apps import apps
import datetime
from typing import List
from django.urls import reverse

from baseclasses import models as baseclass_models
from baseclasses.repositories.db_helper import new_satellite_entry
from baseclasses.dataclasses.view_classes import TabElement, ActionElement

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


def account_view_data(account_id: int, active_sheet: str = ""):
    tabs = (
        TabElement(
            name="Overview", 
            link=reverse('bank_account_view_overview', kwargs={'account_id': account_id}),
            html_id="tab_overview",
        ),
        TabElement(
            name="Transactions", 
            link=reverse('bank_account_view_transactions', kwargs={'account_id': account_id}),
            html_id="tab_transactions",
        ),
        TabElement(
            name="Graphs", 
            link=reverse('bank_account_view_graphs', kwargs={'account_id': account_id}),
            html_id="tab_graphs",
        ),
        TabElement(
            name="Uploads", 
            link=reverse('bank_account_view_uploads', kwargs={'account_id': account_id}),
            html_id="tab_uploads",
        ),
        TabElement(
            name="Transaction Category Map", 
            link=reverse('bank_account_view_transaction_category_map', kwargs={'account_id': account_id}),
            html_id="tab_transaction_category_map",
        ),
    )
    _set_active_tab(tabs, active_sheet)
    actions = (
        ActionElement(
            icon="chevron-left",
            link=reverse('account_list'),
            action_id="list_back",
        ),
        ActionElement(
            icon="trash",
            link=reverse('account_delete_form', kwargs={'account_id': account_id}),
            action_id="delete_account",
        ),
        ActionElement(
            icon="plus",
            link=reverse('transaction_add_form', kwargs={'account_id': account_id}),
            action_id="add_transaction",
        ),
        ActionElement(
            icon="upload",
            link=reverse('upload_transaction_to_account_file', kwargs={'account_id': account_id}),
            action_id="id_transactions_upload",
        ),
    )
    account_statics = account_static_satellite().objects.get(hub_entity=account_id)

    return {
        "tab_elements": tabs,
        "action_elements": actions,
        "account_statics": account_statics,
        "show_date_range_selector": True,
    }


def _set_active_tab(tabs: List[TabElement], active_sheet: str):
    for tab in tabs:
        if tab.html_id == active_sheet:
            tab.active = "active"
        else:
            tab.active = ""



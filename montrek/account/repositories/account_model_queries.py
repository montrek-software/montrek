from django.apps import apps
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



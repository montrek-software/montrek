from django.apps import apps
import datetime
from typing import List

from baseclasses import models as baseclass_models

def account_hub():
    return apps.get_model('account','AccountHub')

def account_static_satellite():
    return apps.get_model('account','AccountStaticSatellite')

def account_credit_institution_link():
    return apps.get_model('link_tables','AccountCreditInstitutionLink')

def credit_institution_hub():
    return apps.get_model('credit_institution','CreditInstitutionHub')

def credit_institution_static_satellite():
    return apps.get_model('credit_institution','CreditInstitutionStaticSatellite')

def new_account(account_name:str,
                account_type:str='Other') -> baseclass_models.MontrekHubABC:
    account_hub_object = account_hub().objects.create()
    account_static_satellite().objects.create(
        hub_entity=account_hub_object,
        account_type=account_type,
        account_name=account_name,
    )
    return account_hub_object


def get_credit_institution_by_account_id(account_id:int) -> baseclass_models.MontrekSatelliteABC:
    account_hub_object = account_hub().objects.get(id=account_id)
    return get_credit_institution_by_account(account_hub_object)

def get_credit_institution_by_account(account_hub_object) -> baseclass_models.MontrekSatelliteABC:
    account_credit_institution_links = account_credit_institution_link().objects.filter(from_hub=account_hub_object)
    credit_institution_hubs = [account_credit_institution_link.to_hub for account_credit_institution_link in account_credit_institution_links]
    credit_institution_satellites = credit_institution_static_satellite().objects.filter(hub_entity__in=credit_institution_hubs)
    return credit_institution_satellites

from django.apps import apps
import datetime
from typing import List

from baseclasses import models as baseclass_models

def account_hub():
    return apps.get_model('account','AccountHub')

def account_static_satellite():
    return apps.get_model('account','AccountStaticSatellite')

def account_transaction_link():
    return apps.get_model('link_tables','AccountTransactionLink')

def transaction_hub():
    return apps.get_model('transaction','TransactionHub')

def transaction_satellite():
    return apps.get_model('transaction','TransactionSatellite')

def account_credit_institution_link():
    return apps.get_model('link_tables','AccountCreditInstitutionLink')

def credit_institution_hub():
    return apps.get_model('credit_institution','CreditInstitutionHub')

def credit_institution_static_satellite():
    return apps.get_model('credit_institution','CreditInstitutionStaticSatellite')

def new_account(account_name:str) -> baseclass_models.MontrekHubABC:
    account_hub_object = account_hub().objects.create()
    account_static_satellite().objects.create(
        hub_entity=account_hub_object,
        account_name=account_name)
    return account_hub_object

def new_transaction_to_account(account_id:int,
                               transaction_date:datetime.date,
                               transaction_amount:int,
                               transaction_price:float,
                               transaction_type:str,
                               transaction_category:str,
                               transaction_description:str) -> None:
    account_hub_object = account_hub().objects.get(id=account_id)
    transaction_hub_object = transaction_hub().objects.create()
    transaction_satellite_object = transaction_satellite().objects.create(
        hub_entity=transaction_hub_object,
        transaction_date=transaction_date,
        transaction_amount=transaction_amount,
        transaction_price=transaction_price,
        transaction_type=transaction_type,
        transaction_category=transaction_category,
        transaction_description=transaction_description)
    account_transaction_link().objects.create(
        from_hub=account_hub_object,
        to_hub=transaction_hub_object)

def get_transactions_by_account_id(account_id:int) -> List[baseclass_models.MontrekSatelliteABC]:
    account_hub_object = account_hub().objects.get(id=account_id)
    return get_transactions_by_account(account_hub_object)

def get_transactions_by_account(account_hub_object) -> List[baseclass_models.MontrekSatelliteABC]:
    account_transaction_links = account_transaction_link().objects.filter(from_hub=account_hub_object)
    transaction_hubs = [account_transaction_link.to_hub for account_transaction_link in account_transaction_links]
    transaction_satellites = transaction_satellite().objects.filter(hub_entity__in=transaction_hubs)
    return transaction_satellites

def get_credit_institution_by_account_id(account_id:int) -> baseclass_models.MontrekSatelliteABC:
    account_hub_object = account_hub().objects.get(id=account_id)
    return get_credit_institution_by_account(account_hub_object)

def get_credit_institution_by_account(account_hub_object) -> baseclass_models.MontrekSatelliteABC:
    account_credit_institution_links = account_credit_institution_link().objects.filter(from_hub=account_hub_object)
    credit_institution_hubs = [account_credit_institution_link.to_hub for account_credit_institution_link in account_credit_institution_links]
    credit_institution_satellites = credit_institution_static_satellite().objects.filter(hub_entity__in=credit_institution_hubs)
    return credit_institution_satellites[0]

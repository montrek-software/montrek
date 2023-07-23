import pandas as pd
from django.apps import apps
from typing import List
import datetime

from baseclasses import models as baseclass_models
from baseclasses.repositories.db_helper import new_link_entry
from baseclasses.repositories.db_helper import new_satellite_entry
from baseclasses.repositories.db_helper import get_link_to_hub
from baseclasses.repositories.db_helper import select_satellite
from baseclasses.repositories.db_helper import get_hubs_by_satellite_attribute

def account_hub():
    return apps.get_model('account','AccountHub')

def transaction_hub():
    return apps.get_model('transaction','TransactionHub')

def transaction_satellite():
    return apps.get_model('transaction','TransactionSatellite')

def account_transaction_link():
    return apps.get_model('link_tables','AccountTransactionLink')

def transaction_transaction_type_link():
    return apps.get_model('transaction','TransactionTransactionTypeLink')

def transaction_type_satellite():
    return apps.get_model('transaction','TransactionTypeSatellite')

def new_transaction_to_account(account_id:int,
                               transaction_date:datetime.date,
                               transaction_amount:int,
                               transaction_price:float,
                               transaction_type:str,
                               transaction_category:str,
                               transaction_description:str) -> None:
    account_hub_object = account_hub().objects.get(id=account_id)
    transaction_hub_object = transaction_hub().objects.create()
    transaction_satellite_object = new_satellite_entry( 
        hub_entity=transaction_hub_object,
        satellite_class=transaction_satellite(),
        transaction_date=transaction_date,
        transaction_amount=transaction_amount,
        transaction_price=transaction_price,
        transaction_type=transaction_type,
        transaction_category=transaction_category,
        transaction_description=transaction_description)
    new_link_entry(account_hub_object, 
                   transaction_hub_object,
                  account_transaction_link())

def new_transactions_to_account_from_df(account_hub:baseclass_models.MontrekHubABC,
                                        import_df: pd.DataFrame) -> None:
    expected_columns = ['transaction_date', 'transaction_amount', 'transaction_price', 'transaction_type', 'transaction_category', 'transaction_description']
    if not all([column in import_df.columns for column in expected_columns]):
        raise KeyError(f'Wrong columns in dataframe\n\tGot: {import_df.columns}\n\tExpected: {expected_columns}')

def get_transactions_by_account_id(account_id:int) -> List[baseclass_models.MontrekSatelliteABC]:
    account_hub_object = account_hub().objects.get(id=account_id)
    return get_transactions_by_account(account_hub_object)

def get_transactions_by_account(account_hub_object) -> List[baseclass_models.MontrekSatelliteABC]:
    account_transaction_links = account_transaction_link().objects.filter(from_hub=account_hub_object)
    transaction_hubs = [account_transaction_link.to_hub for account_transaction_link in account_transaction_links]
    transaction_satellites = transaction_satellite().objects.filter(hub_entity__in=transaction_hubs)
    return transaction_satellites

def get_transaction_type_by_transaction(transaction_satellite_object: baseclass_models.MontrekSatelliteABC) -> str:
    transaction_hub = transaction_satellite_object.hub_entity
    try:
        transaction_type_hub = get_link_to_hub(from_hub=transaction_hub,
                                               link_table=transaction_transaction_type_link())
    except transaction_transaction_type_link().DoesNotExist:
        transaction_type_hub = _set_transaction_type_by_value(
            transaction_satellite_object
        )
    return select_satellite(
        hub_entity=transaction_type_hub,
        satellite_class=transaction_type_satellite())

def set_transaction_type(transaction_satellite_object: baseclass_models.MontrekSatelliteABC,
                         value: str = None) -> None:
    if value is None:
        _set_transaction_type_by_value(transaction_satellite_object)
    else:
        transaction_type_hub = get_hubs_by_satellite_attribute(
            transaction_type_satellite(),
            'typename',
            value)[0]
        new_link_entry(
            from_hub=transaction_satellite_object.hub_entity,
            to_hub=transaction_type_hub,
            link_table=transaction_transaction_type_link())


def _set_transaction_type_by_value(transaction_satellite_object: baseclass_models.MontrekSatelliteABC,
                                  ) -> baseclass_models.MontrekHubABC:
    transaction_value = transaction_satellite_object.transaction_value
    if transaction_value >= 0:
        transaction_type_hub = get_hubs_by_satellite_attribute(
            transaction_type_satellite(),
            'typename',
            'INCOME')[0]
    else:
        transaction_type_hub = get_hubs_by_satellite_attribute(
            transaction_type_satellite(),
            'typename',
            'EXPANSE')[0]
    new_link_entry(
        from_hub=transaction_satellite_object.hub_entity,
        to_hub=transaction_type_hub,
        link_table=transaction_transaction_type_link())
    return transaction_type_hub


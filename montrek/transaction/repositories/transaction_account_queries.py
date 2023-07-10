import pandas as pd
from django.apps import apps
from django.db.models import Q
from typing import List
import datetime

from baseclasses import models as baseclass_models
from baseclasses.repositories.db_helper import new_link_entry
from baseclasses.repositories.db_helper import new_satellite_entry
from baseclasses.repositories.db_helper import new_satellites_bunch_from_df_and_from_hub_link

def account_hub():
    return apps.get_model('account','AccountHub')

def transaction_hub():
    return apps.get_model('transaction','TransactionHub')

def transaction_satellite():
    return apps.get_model('transaction','TransactionSatellite')

def account_transaction_link():
    return apps.get_model('link_tables','AccountTransactionLink')

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

def new_transactions_to_account_from_df(account_hub_object: baseclass_models.MontrekSatelliteABC,
                                        transaction_df: pd.DataFrame) -> List[baseclass_models.MontrekSatelliteABC]:
    expected_columns = ['transaction_date',
                        'transaction_amount',
                        'transaction_price',
                        'transaction_type',
                        'transaction_category',
                        'transaction_description']
    if not all([column in transaction_df.columns for column in expected_columns]):
        expected_columns_str = ', '.join(expected_columns)
        got_columns_str = ', '.join(transaction_df.columns)
        raise KeyError(
            f'Wrong columns in transaction_df\n\tGot: {got_columns_str}\n\tExpected: {expected_columns_str}')
    transaction_satellites = new_satellites_bunch_from_df_and_from_hub_link(
        satellite_class=transaction_satellite(),
        import_df=transaction_df,
        from_hub=account_hub_object,
        link_table_class=account_transaction_link())
    return transaction_satellites

def get_transactions_by_account_id(account_id:int) -> List[baseclass_models.MontrekSatelliteABC]:
    account_hub_object = account_hub().objects.get(id=account_id)
    return get_transactions_by_account_hub(account_hub_object)

def get_transactions_by_account_hub(account_hub_object,
                                    reference_date:datetime.datetime=datetime.datetime.now()
                                   ) -> List[baseclass_models.MontrekSatelliteABC]:
    account_transaction_links = account_transaction_link().objects.filter(from_hub=account_hub_object)
    transaction_hubs = [account_transaction_link.to_hub for account_transaction_link in account_transaction_links]
    transaction_satellites = (transaction_satellite().objects
                              .filter(Q(hub_entity__in=transaction_hubs) &
                                      Q(state_date_start__lte = reference_date) &
                                      Q(state_date_end__gt = reference_date) 
                                     )
                             )
    return transaction_satellites

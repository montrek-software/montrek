import datetime
from typing import List

from .models import AccountHub
from transaction.models import TransactionHub
from transaction.models import TransactionSatellite 
from link_tables.models import AccountTransactionLink

def new_transaction_to_account(account_id:int,
                               transaction_date:datetime.date,
                               transaction_amount:int,
                               transaction_price:float,
                               transaction_type:str,
                               transaction_category:str,
                               transaction_description:str) -> None:
    account_hub = AccountHub.objects.get(id=account_id)
    transaction_hub = TransactionHub.objects.create()
    transaction_satellite = TransactionSatellite.objects.create(
        hub_entity=transaction_hub,
        transaction_date=transaction_date,
        transaction_amount=transaction_amount,
        transaction_price=transaction_price,
        transaction_type=transaction_type,
        transaction_category=transaction_category,
        transaction_description=transaction_description)
    AccountTransactionLink.objects.create(
        from_hub=account_hub,
        to_hub=transaction_hub)

def get_transactions_by_account_id(account_id:int) -> List[TransactionSatellite]:
    account_hub = AccountHub.objects.get(id=account_id)
    account_transaction_links = AccountTransactionLink.objects.filter(from_hub=account_hub)
    transaction_hubs = [account_transaction_link.to_hub for account_transaction_link in account_transaction_links]
    transaction_satellites = TransactionSatellite.objects.filter(hub_entity__in=transaction_hubs)
    return transaction_satellites

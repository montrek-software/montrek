import pandas as pd
from django.apps import apps
from typing import List
import datetime

from baseclasses import models as baseclass_models
from baseclasses.repositories.db_helper import new_link_entry
from baseclasses.repositories.db_helper import new_satellite_entry
from baseclasses.repositories.db_helper import select_satellite
from baseclasses.repositories.db_helper import get_hubs_by_satellite_attribute


def account_hub():
    return apps.get_model("account", "AccountHub")


def transaction_hub():
    return apps.get_model("transaction", "TransactionHub")


def transaction_satellite():
    return apps.get_model("transaction", "TransactionSatellite")



def new_transaction_to_account(
    account_id: int,
    transaction_date: datetime.date,
    transaction_amount: int,
    transaction_price: float,
    transaction_type: str,
    transaction_category: str,
    transaction_description: str,
) -> None:
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
        transaction_description=transaction_description,
    )
    new_link_entry(
        account_hub_object, transaction_hub_object, account_transaction_link()
    )


def new_transactions_to_account_from_df(
    account_hub: baseclass_models.MontrekHubABC, import_df: pd.DataFrame
) -> None:
    expected_columns = [
        "transaction_date",
        "transaction_amount",
        "transaction_price",
        "transaction_type",
        "transaction_category",
        "transaction_description",
    ]
    if not all([column in import_df.columns for column in expected_columns]):
        raise KeyError(
            f"Wrong columns in dataframe\n\tGot: {import_df.columns}\n\tExpected: {expected_columns}"
        )





import pandas as pd
from django.apps import apps
from django.db.models import Q
from django.core.paginator import Paginator
from typing import List
import datetime

from baseclasses import models as baseclass_models
from baseclasses.repositories.db_helper import new_link_entry
from baseclasses.repositories.db_helper import new_satellite_entry
from baseclasses.repositories.db_helper import select_satellite
from baseclasses.repositories.db_helper import (
    new_satellites_bunch_from_df_and_from_hub_link,
)
from transaction.repositories.transaction_type_queries import set_transaction_type
from transaction.repositories.transaction_model_queries import add_asset_to_transaction
from asset.repositories.asset_queries import find_asset_hub_by_isin_or_create

def account_hub():
    return apps.get_model("account", "AccountHub")


def transaction_hub():
    return apps.get_model("transaction", "TransactionHub")


def transaction_satellite():
    return apps.get_model("transaction", "TransactionSatellite")

def transaction_category_map_satellite():
    return apps.get_model("transaction", "TransactionCategoryMapSatellite")

def asset_static_satellite():
    return apps.get_model("asset", "AssetStaticSatellite")

def new_transaction_to_account(
    account_id: int,
    transaction_date: datetime.date,
    transaction_amount: int,
    transaction_price: float,
    transaction_category: str,
    transaction_description: str,
    transaction_type: str = None,
) -> baseclass_models.MontrekHubABC:
    account_hub_object = account_hub().objects.get(id=account_id)
    transaction_hub_object = transaction_hub().objects.create()
    transaction_satellite_object = new_satellite_entry(
        hub_entity=transaction_hub_object,
        satellite_class=transaction_satellite(),
        transaction_date=transaction_date,
        transaction_amount=float(transaction_amount),
        transaction_price=float(transaction_price),
        transaction_description=transaction_description,
    )
    new_link_entry(
        account_hub_object,
        transaction_hub_object,
        "link_account_transaction",
    )
    set_transaction_type(transaction_satellite_object, transaction_type)
    return transaction_hub_object

def new_transaction_to_account_with_asset(
    account_id: int,
    transaction_date: datetime.date,
    transaction_amount: int,
    transaction_price: float,
    transaction_category: str,
    transaction_description: str,
    transaction_type: str,
    asset_isin: str,
    asset_wkn: str,
    asset_name: str,
    asset_type: str,
) -> baseclass_models.MontrekHubABC:
    transaction_hub = new_transaction_to_account(
        account_id,
        transaction_date,
        transaction_amount,
        transaction_price,
        transaction_category,
        transaction_description,
        transaction_type,
    )
    asset_hub, created = find_asset_hub_by_isin_or_create(asset_isin)
    if created:
        created_asset_static_satellite = select_satellite(
            asset_hub, asset_static_satellite()
        )
        created_asset_static_satellite.asset_name = asset_name
        created_asset_static_satellite.asset_wkn = asset_wkn
        created_asset_static_satellite.asset_type = asset_type
        created_asset_static_satellite.save()
    add_asset_to_transaction(asset_hub, transaction_hub)
    return transaction_hub




def new_transactions_to_account_from_df(
    account_hub_object: baseclass_models.MontrekSatelliteABC,
    transaction_df: pd.DataFrame,
) -> List[baseclass_models.MontrekSatelliteABC]:
    expected_columns = [
        "transaction_date",
        "transaction_amount",
        "transaction_price",
        "transaction_description",
        "transaction_party",
        "transaction_party_iban",
    ]
    if not all([column in transaction_df.columns for column in expected_columns]):
        expected_columns_str = ", ".join(expected_columns)
        got_columns_str = ", ".join(transaction_df.columns)
        raise KeyError(
            f"Wrong columns in transaction_df\n\tGot: {got_columns_str}\n\tExpected: {expected_columns_str}"
        )
    transaction_satellites = new_satellites_bunch_from_df_and_from_hub_link(
        satellite_class=transaction_satellite(),
        import_df=transaction_df,
        from_hub=account_hub_object,
        related_field="link_account_transaction",
    )
    return transaction_satellites


def get_transactions_by_account_id(
    account_id: int,
) -> List[baseclass_models.MontrekSatelliteABC]:
    account_hub_object = account_hub().objects.get(id=account_id)
    return get_transactions_by_account_hub(account_hub_object)


def get_transactions_by_account_hub(
    account_hub_object, reference_date: datetime.datetime = datetime.datetime.now()
) -> List[baseclass_models.MontrekSatelliteABC]:
    transaction_hubs = account_hub_object.link_account_transaction.all()
    transaction_satellites = transaction_satellite().objects.filter(
        Q(hub_entity__in=transaction_hubs)
        & Q(state_date_start__lte=reference_date)
        & Q(state_date_end__gt=reference_date)
    )
    return transaction_satellites

def get_paginated_transactions(account_id, start_date, end_date, page_number=1, paginate_by=10):
    transactions = get_transactions_by_account_id(account_id)
    transactions = transactions.filter(
        Q(transaction_date__gte=start_date)
        & Q(transaction_date__lte=end_date)
    )
    paginator = Paginator(transactions.order_by("-transaction_date").all(), paginate_by)
    page = paginator.get_page(page_number)
    return page

def get_transaction_category_map_by_account_id(account_id):
    account_hub_object = account_hub().objects.get(id=account_id)
    return get_transaction_category_map_by_account_hub(account_hub_object)

def get_transaction_category_map_by_account_hub(account_hub_object, reference_date = datetime.datetime.now()):
    transaction_category_map_hubs = account_hub_object.link_account_transaction_category_map.filter(
        is_deleted=False
    )
    transaction_category_map_satellites = transaction_category_map_satellite().objects.filter( 
        Q(hub_entity__in=transaction_category_map_hubs)
        & Q(state_date_start__lte=reference_date)
        & Q(state_date_end__gt=reference_date)
    )
    return transaction_category_map_satellites


def get_paginated_transactions_category_map(account_id, page_number=1, paginate_by=10):
   transaction_category_map = get_transaction_category_map_by_account_id(account_id) 
   paginator = Paginator(transaction_category_map.order_by("category").all(), paginate_by)
   page = paginator.get_page(page_number)
   return page


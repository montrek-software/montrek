import pandas as pd
from django.apps import apps
from typing import List
import datetime

from baseclasses import models as baseclass_models
from baseclasses.repositories.db_helper import new_link_entry
from baseclasses.repositories.db_helper import new_satellite_entry
from baseclasses.repositories.db_helper import select_satellite
from baseclasses.repositories.db_helper import get_hubs_by_satellite_attribute



def transaction_hub():
    return apps.get_model("transaction", "TransactionHub")


def transaction_satellite():
    return apps.get_model("transaction", "TransactionSatellite")

def asset_hub():
    return apps.get_model("asset", "AssetHub")

def asset_static_satellite():
    return apps.get_model("asset", "AssetStaticSatellite")




def add_asset_to_transaction(
    asset_hub: baseclass_models.MontrekHubABC,
    transaction_hub: baseclass_models.MontrekHubABC,
) -> None:
    new_link_entry(
        transaction_hub,
        asset_hub,
        "link_transaction_asset",
    )

def get_transaction_asset_hub(
    transaction_hub: baseclass_models.MontrekHubABC,
) -> baseclass_models.MontrekHubABC:
    return transaction_hub.link_transaction_asset.first()

def get_transaction_asset_satellite(
    transaction_hub: baseclass_models.MontrekHubABC,
) -> baseclass_models.MontrekHubABC:
    asset_hub = get_transaction_asset_hub(transaction_hub)
    return select_satellite(asset_hub, asset_static_satellite())



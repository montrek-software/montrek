from typing import List
from django.apps import apps
from baseclasses.repositories.db_helper import select_satellite


def currency_hub():
    return apps.get_model("currency", "CurrencyHub")


def currency_select_satellite():
    return apps.get_model("currency", "CurrencyStaticSatellite")


def get_all_currency_codes_from_db() -> List[str]:
    currency_hubs = currency_hub().objects.all()
    currency_codes = [
        select_satellite(hub, currency_select_satellite()).ccy_code
        for hub in currency_hubs
    ]
    return currency_codes

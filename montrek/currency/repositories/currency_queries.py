from typing import List
from django.apps import apps
from django.utils import timezone
from baseclasses.repositories.db_helper import select_satellite
from currency.repositories.currency_repository import CurrencyRepositories


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

def add_fx_rate_to_ccy(ccy:str, value_date: timezone.datetime, fx_rate: float):
    ccy_hub = currency_select_satellite().objects.get(ccy_code=ccy).hub_entity
    currency_repo = CurrencyRepositories(ccy_hub)
    currency_repo.add_fx_rate(fx_rate, value_date)

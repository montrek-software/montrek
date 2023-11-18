from django.utils import timezone
from django.apps import apps
from django.db.models import Q
from currency.models import CurrencyHub
from currency.models import CurrencyTimeSeriesSatellite
from baseclasses.repositories.db_helper import new_satellite_entry, select_satellite


def currency_time_series_satellite():
    return apps.get_model("currency", "CurrencyTimeSeriesSatellite")


def add_fx_rate_to_ccy(ccy:str, value_date: timezone.datetime, fx_rate: float):
    currency_hub = CurrencyHub.objects.get(ccy_code=ccy)
    currency_repo = CurrencyRepositories(currency_hub)
    fx_rate = 1.23
    currency_repo.add_fx_rate(fx_rate, value_date)

class CurrencyRepositories:
    def __init__(self, currency_hub: CurrencyHub):
        self.currency_hub = currency_hub

    def add_fx_rate_now(self, fx_rate: float):
        self.add_fx_rate(fx_rate, timezone.now().date())

    def add_fx_rate(self, fx_rate: float, value_date: timezone.datetime):
        new_satellite_entry(
            CurrencyTimeSeriesSatellite,
            self.currency_hub,
            fx_rate=fx_rate,
            value_date=value_date,
        )

    def get_fx_rate(self, value_date: timezone.datetime) -> float:
        currency_time_series = select_satellite(
            self.currency_hub,
            currency_time_series_satellite(),
            applied_filter=Q(value_date=value_date),
        )
        return currency_time_series.fx_rate

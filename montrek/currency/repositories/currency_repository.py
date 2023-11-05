from django.utils import timezone
from currency.models import CurrencyHub
from currency.models import CurrencyTimeSeriesSatellite
from baseclasses.repositories.db_helper import new_satellite_entry


class CurrencyRepositories:
    def __init__(self, currency_hub: CurrencyHub):
        self.currency_hub = currency_hub

    def add_fx_rate_now(self, fx_rate: float):
        new_satellite_entry(
            CurrencyTimeSeriesSatellite,
            self.currency_hub,
            fx_rate=fx_rate,
            value_date=timezone.now().date(),
        )

    def get_fx_rate(self, value_date: timezone.datetime) -> float:
        pass

from django.utils import timezone
from django.apps import apps
from django.db.models import Q, F, OuterRef, Subquery
from django.db.models import QuerySet, DurationField, ExpressionWrapper
from currency.models import CurrencyHub
from currency.models import CurrencyTimeSeriesSatellite
from currency.models import CurrencyStaticSatellite
from baseclasses.repositories.db_helper import new_satellite_entry, select_satellite
from baseclasses.repositories.montrek_repository import MontrekRepository

def currency_time_series_satellite():
    return apps.get_model("currency", "CurrencyTimeSeriesSatellite")

class CurrencyRepository(MontrekRepository):
    hub_class = CurrencyHub

    def std_queryset(self, **kwargs) -> QuerySet:
        self.add_satellite_fields_annotations(
            CurrencyStaticSatellite,
            ["ccy_name", "ccy_code"],
            self.reference_date,
        )
        return self.build_queryset()

    def last_fx_rate_queryset(self, **kwargs) -> QuerySet:
        self.add_last_ts_satellite_fields_annotations(
            CurrencyTimeSeriesSatellite,
            ["fx_rate"],
            self.reference_date,
        )
        return self.std_queryset(**kwargs)


#TODO: Move to CurrencyRepository
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

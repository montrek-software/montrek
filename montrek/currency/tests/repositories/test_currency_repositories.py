import datetime
from django.test import TestCase
from django.utils import timezone
from django.db.models import Q
from currency.tests.factories.currency_factories import (
    CurrencyHubFactory,
    CurrencyTimeSeriesSatelliteFactory,
)
from currency.models import CurrencyTimeSeriesSatellite
from currency.repositories.currency_repository import CurrencyRepositories


class TestCurrencyRepositoroes(TestCase):
    def test_add_fx_rate_now(self):
        currency_hub = CurrencyHubFactory()
        currency_repo = CurrencyRepositories(currency_hub)
        fx_rate = 1.23
        currency_repo.add_fx_rate_now(fx_rate)
        currency_time_series_satellite = CurrencyTimeSeriesSatellite.objects.last()
        self.assertEqual(float(currency_time_series_satellite.fx_rate), fx_rate)
        self.assertEqual(currency_time_series_satellite.hub_entity, currency_hub)
        self.assertEqual(
            currency_time_series_satellite.value_date, timezone.now().date()
        )

    def _setup_update_fx_rate(
        self, fx_rate_1: float, fx_rate_2: float
    ) -> CurrencyTimeSeriesSatelliteFactory:
        currency_time_series_factory = CurrencyTimeSeriesSatelliteFactory.create(
            fx_rate=fx_rate_1,
            value_date=timezone.now().date(),
        )
        currency_repo = CurrencyRepositories(currency_time_series_factory.hub_entity)
        currency_repo.add_fx_rate_now(fx_rate_2)
        return currency_time_series_factory

    def test_add_fx_rate_now_update_value_date(self):
        fx_rate_1 = 1.23
        fx_rate_2 = 2.34
        currency_time_series_factory = self._setup_update_fx_rate(fx_rate_1, fx_rate_2)
        currency_time_series_satellite = CurrencyTimeSeriesSatellite.objects.get(
            Q(hub_entity=currency_time_series_factory.hub_entity)
            & Q(state_date_end__gt=timezone.now())
        )
        self.assertEqual(float(currency_time_series_satellite.fx_rate), fx_rate_2)

    def test_get_fx_rate(self):
        fx_rate_1 = 1.23
        fx_rate_2 = 2.34
        currency_time_series_factory = self._setup_update_fx_rate(fx_rate_1, fx_rate_2)
        currency_repo = CurrencyRepositories(currency_time_series_factory.hub_entity)
        self.assertEqual(float(currency_repo.get_fx_rate(timezone.now())), fx_rate_2)

    def test_get_fx_multiple_days(self):
        fx_rate_1 = 1.23
        fx_rate_2 = 2.34
        date_1 = timezone.datetime(2023, 11, 1)
        date_2 = timezone.datetime(2023, 10, 11)
        currency_hub = CurrencyHubFactory()
        CurrencyTimeSeriesSatelliteFactory.create(
            hub_entity=currency_hub,
            fx_rate=fx_rate_1,
            value_date=date_1,
        )
        CurrencyTimeSeriesSatelliteFactory.create(
            hub_entity=currency_hub,
            fx_rate=fx_rate_2,
            value_date=date_2,
        )
        currency_repo = CurrencyRepositories(currency_hub)
        self.assertEqual(float(currency_repo.get_fx_rate(date_1)), fx_rate_1)
        self.assertEqual(float(currency_repo.get_fx_rate(date_2)), fx_rate_2)

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

    def test_add_fx_rate_now_update_value_date(self):
        fx_rate_1 = 1.23
        currency_time_series_factory = CurrencyTimeSeriesSatelliteFactory.create(
            fx_rate=fx_rate_1,
            value_date=timezone.now().date(),
        )
        fx_rate_2 = 2.56
        currency_repo = CurrencyRepositories(currency_time_series_factory.hub_entity)
        currency_repo.add_fx_rate_now(fx_rate_2)
        currency_time_series_satellite = CurrencyTimeSeriesSatellite.objects.get(
            Q(hub_entity=currency_time_series_factory.hub_entity)
            & Q(state_date_end__gt=timezone.now())
        )
        self.assertEqual(float(currency_time_series_satellite.fx_rate), fx_rate_2)

from django.test import TestCase
from currency.tests.factories.currency_factories import (
    CurrencyStaticSatelliteFactory,
    CurrencyTimeSeriesSatelliteFactory,
)
from currency.models import CurrencyHub


class TestCurrencyModels(TestCase):
    def test_static_satellite_hub(self):
        static_satellite = CurrencyStaticSatelliteFactory()
        self.assertTrue(isinstance(static_satellite.hub_entity, CurrencyHub))

    def test_time_series_satellite_hub(self):
        time_series_satellite = CurrencyTimeSeriesSatelliteFactory()
        self.assertTrue(isinstance(time_series_satellite.hub_entity, CurrencyHub))

from django.test import TestCase
from django.utils import timezone
from currency.tests.factories.currency_factories import CurrencyStaticSatelliteFactory
from currency.repositories.currency_queries import get_all_currency_codes_from_db
from currency.repositories.currency_queries import add_fx_rate_to_ccy
from currency.models import CurrencyTimeSeriesSatellite


TEST_CURRENCY_CODES = ["USD", "EUR", "GBP"]


class TestGetCurrencyHubs(TestCase):
    @classmethod
    def setUpTestData(cls):
        for ccy in TEST_CURRENCY_CODES:
            CurrencyStaticSatelliteFactory(ccy_code=ccy)

    def test_get_currency_codes_from_db(self):
        currency_codes = get_all_currency_codes_from_db()
        self.assertEqual(currency_codes, TEST_CURRENCY_CODES)

    def test_add_fx_rate_to_ccy(self):
        value_date = timezone.datetime(2023, 11, 1)
        for currency in TEST_CURRENCY_CODES:
            add_fx_rate_to_ccy(currency, value_date, 1.0)
            currency_time_series_model = CurrencyTimeSeriesSatellite.objects.last()
            self.assertEqual(currency_time_series_model.value_date, value_date.date())
            self.assertEqual(currency_time_series_model.fx_rate, 1.0)

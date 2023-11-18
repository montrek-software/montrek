from django.test import TestCase
from currency.tests.factories.currency_factories import CurrencyStaticSatelliteFactory
from currency.repositories.currency_queries import get_all_currency_codes_from_db

TEST_CURRENCY_CODES = ["USD", "EUR", "GBP"]


class TestGetCurrencyHubs(TestCase):
    @classmethod
    def setUpTestData(cls):
        for ccy in TEST_CURRENCY_CODES:
            CurrencyStaticSatelliteFactory(ccy_code=ccy)

    def test_get_currency_codes_from_db(self):
        currency_codes = get_all_currency_codes_from_db()
        self.assertEqual(currency_codes, TEST_CURRENCY_CODES)

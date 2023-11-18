from typing import List, Dict
import decimal
import datetime
from django.test import TestCase
from django.utils import timezone
from currency.managers.fx_rate_update_strategy import (
    FxRateUpdateStrategy,
    YahooFxRateUpdateStrategy,
)
from currency.tests.factories.currency_factories import CurrencyStaticSatelliteFactory
from currency.repositories.currency_repository import CurrencyRepositories
from currency.models import CurrencyHub
from currency.models import CurrencyStaticSatellite
from baseclasses.repositories.db_helper import select_satellite

TEST_CURRENCY_CODES = ["USD", "EUR", "GBP"]


class FxRateUpdateStrategy_TestClass(FxRateUpdateStrategy):
    def _get_fx_rates_from_source(
        self,
        currency_code_list: List[str],
        value_date: timezone.datetime,
    ) -> Dict[str, float]:
        return {ccy: 1.0 for ccy in currency_code_list}


class TestFxRateUpdateStrategy(TestCase):
    @classmethod
    def setUpTestData(cls):
        for ccy in TEST_CURRENCY_CODES:
            CurrencyStaticSatelliteFactory(ccy_code=ccy)
        cls.test_time = timezone.datetime(2023, 11, 18)

    def test_get_update_fx_rates_not_implemented(self):
        with self.assertRaises(NotImplementedError) as error:
            FxRateUpdateStrategy().update_fx_rates(self.test_time)
        self.assertEqual(
            str(error.exception),
            "FxRateUpdateStrategy must implement _get_fx_rates_from_source()",
        )

    def test_right_currencies(self):
        strategy = FxRateUpdateStrategy_TestClass()
        strategy.update_fx_rates(self.test_time)

        for currency_hub in CurrencyHub.objects.all():
            self.assertEqual(
                CurrencyRepositories(currency_hub).get_fx_rate(self.test_time), 1.0
            )


class TestYahooFxRateUpdateStrategy(TestFxRateUpdateStrategy):
    def test_get_fx_rates_from_source(self):
        strategy = YahooFxRateUpdateStrategy()
        strategy.update_fx_rates(self.test_time)
        expected_rates = {'USD': 0.916, 'EUR': 1.0, 'GBP': 1.1417}
        for currency_hub in CurrencyHub.objects.all():
            ccy_code = select_satellite(currency_hub, CurrencyStaticSatellite).ccy_code
            self.assertAlmostEqual(
                CurrencyRepositories(currency_hub).get_fx_rate(self.test_time),
                decimal.Decimal(expected_rates[ccy_code]),
            )

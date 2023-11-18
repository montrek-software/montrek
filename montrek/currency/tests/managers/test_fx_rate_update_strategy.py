from typing import List, Dict
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
from baseclasses.repositories.db_helper import select_satellite

TEST_CURRENCY_CODES = ["USD", "EUR", "GBP"]


class FxRateUpdateStrategy_TestClass(FxRateUpdateStrategy):
    def _get_fx_rates_from_source(
        self, currency_code_list: List[str]
    ) -> Dict[str, float]:
        return {ccy: 1.0 for ccy in currency_code_list}


class TestRxRateUpdateStrategy(TestCase):
    @classmethod
    def setUpTestData(cls):
        for ccy in TEST_CURRENCY_CODES:
            CurrencyStaticSatelliteFactory(ccy_code=ccy)

    def test_get_update_fx_rates_not_implemented(self):
        with self.assertRaises(NotImplementedError) as error:
            FxRateUpdateStrategy().update_fx_rates()
        self.assertEqual(
            str(error.exception),
            "FxRateUpdateStrategy must implement _get_fx_rates_from_source()",
        )

    def test_right_currencies(self):
        test_time = timezone.datetime(2023, 11, 18)
        strategy = FxRateUpdateStrategy_TestClass()
        strategy.update_fx_rates(test_time)

        for currency_hub in CurrencyHub.objects.all():
            self.assertEqual(
                CurrencyRepositories(currency_hub).get_fx_rate(test_time), 1.0
            )

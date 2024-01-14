from typing import List, Dict
import decimal
from django.test import TestCase
from django.utils import timezone
from currency.managers.fx_rate_update_strategy import (
    FxRateUpdateStrategy,
    YahooFxRateUpdateStrategy,
)
from currency.tests.factories.currency_factories import CurrencyStaticSatelliteFactory
from currency.repositories.currency_repository import CurrencyRepository
from baseclasses.utils import montrek_time

TEST_CURRENCY_CODES = ["USD", "EUR", "GBP"]


class FxRateUpdateStrategyTestClass(FxRateUpdateStrategy):
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
        cls.test_time = timezone.datetime(2023, 11, 28)

    def test_get_update_fx_rates_not_implemented(self):
        with self.assertRaises(NotImplementedError) as error:
            FxRateUpdateStrategy().update_fx_rates(self.test_time)
        self.assertEqual(
            str(error.exception),
            "FxRateUpdateStrategy must implement _get_fx_rates_from_source()",
        )

    def test_right_currencies(self):
        strategy = FxRateUpdateStrategyTestClass()
        strategy.update_fx_rates(self.test_time)

        for currency_hub in CurrencyRepository().std_queryset().all():
            self.assertEqual(
                currency_hub.fx_rate, 1.0
            )


class TestYahooFxRateUpdateStrategy(TestFxRateUpdateStrategy):
    def test_get_fx_rates_from_source(self):
        strategy = YahooFxRateUpdateStrategy()
        strategy.update_fx_rates(self.test_time)
        expected_rates = {'USD': 0.9125, 'EUR': 1.0, 'GBP': 1.1529}
        for currency_hub in CurrencyRepository().std_queryset().all():
            ccy_code = currency_hub.ccy_code
            self.assertAlmostEqual(
                currency_hub.fx_rate,
                decimal.Decimal(expected_rates[ccy_code]),
            )

    #def test_get_fx_rates_on_weekends(self):
    #    strategy = YahooFxRateUpdateStrategy()
    #    strategy.update_fx_rates(montrek_time(2024,1,14)) # Sunday
    #    for currency_hub in CurrencyHub.objects.all():
    #        ccy_code = select_satellite(currency_hub, CurrencyStaticSatellite).ccy_code
    #        ccy_code.value_date.weekday() == 5

    #    strategy.update_fx_rates(montrek_time(2024,1,13)) # Saturday
    #    for currency_hub in CurrencyHub.objects.all():
    #        ccy_code = select_satellite(currency_hub, CurrencyStaticSatellite).ccy_code
    #        ccy_code.value_date.weekday() == 5

    #    strategy.update_fx_rates(montrek_time(2024,1,11)) # Thursday
    #    for currency_hub in CurrencyHub.objects.all():
    #        ccy_code = select_satellite(currency_hub, CurrencyStaticSatellite).ccy_code
    #        ccy_code.value_date.weekday() == 4

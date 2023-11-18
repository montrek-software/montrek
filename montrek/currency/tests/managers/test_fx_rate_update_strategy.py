from typing import List, Dict
from django.test import TestCase
from currency.managers.fx_rate_update_strategy import FxRateUpdateStrategy, YahooFxRateUpdateStrategy
from currency.tests.factories.currency_factories import CurrencyStaticSatelliteFactory

class FxRateUpdateStrategy_TestClass(FxRateUpdateStrategy):
    def _get_fx_rates_from_source(self, currency_code_list: List[str]) -> Dict[str, float]:
        pass

class TestRxRateUpdateStrategy(TestCase):
    @classmethod
    def setUpTestData(cls):
        for ccy in ['USD', 'EUR', 'GBP']:
            CurrencyStaticSatelliteFactory(ccy_code=ccy)



    def test_get_update_fx_rates_not_implemented(self):
        with self.assertRaises(NotImplementedError) as error:
            FxRateUpdateStrategy().update_fx_rates()
        self.assertEqual(str(error.exception), 'FxRateUpdateStrategy must implement _get_fx_rates_from_source()')


from django.test import TestCase
from currency.managers.fx_rate_update_factory import FxRateUpdateFactory
from currency.managers.fx_rate_update_strategy import YahooFxRateUpdateStrategy


class FxRateUpdateFactoryTest(TestCase):
    def test_get_fx_rate_upload_strategy_unkown(self):
        with self.assertRaises(ValueError) as error:
            FxRateUpdateFactory.get_fx_rate_update_strategy('Unknown')
            self.assertEqual(str(error.exception), 'Unknown fx rate upload strategy for Unknown')


    def test_get_fx_rate_upload_strategy_yahoo(self):
        self.assertTrue(isinstance(FxRateUpdateFactory.get_fx_rate_update_strategy('Yahoo'), YahooFxRateUpdateStrategy))

from typing import List, Dict
from django.utils import timezone
from currency.repositories.currency_queries import get_all_currency_codes_from_db


class FxRateUpdateStrategy:
    def update_fx_rates(self, value_date: timezone.datetime):
        currency_code_list = get_all_currency_codes_from_db()
        fx_rates = self._get_fx_rates_from_source(currency_code_list)
        return fx_rates

    def _get_fx_rates_from_source(
        self, currency_code_list: List[str]
    ) -> Dict[str, float]:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _get_fx_rates_from_source()"
        )


class YahooFxRateUpdateStrategy(FxRateUpdateStrategy):
    def _get_fx_rates_from_source(
        self, currency_code_list: List[str]
    ) -> Dict[str, float]:
        # Code to get fx rates from yahoo and stored them in the database
        pass

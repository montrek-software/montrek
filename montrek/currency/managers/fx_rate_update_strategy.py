from typing import List, Dict
from django.utils import timezone
import yfinance as yf
from currency.repositories.currency_queries import get_all_currency_codes_from_db
from currency.repositories.currency_queries import add_fx_rate_to_ccy


class FxRateUpdateStrategy:
    def update_fx_rates(self, value_date: timezone.datetime):
        currency_code_list = get_all_currency_codes_from_db()
        fx_rates = self._get_fx_rates_from_source(currency_code_list, value_date)
        self._add_fx_rates_to_db(fx_rates, value_date)

    def _get_fx_rates_from_source(
        self,
        currency_code_list: List[str],
        value_date: timezone.datetime,
    ) -> Dict[str, float]:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _get_fx_rates_from_source()"
        )

    def _add_fx_rates_to_db(
        self, fx_rates: Dict[str, float], value_date: timezone.datetime
    ):
        for ccy, fx_rate in fx_rates.items():
            add_fx_rate_to_ccy(ccy, value_date, fx_rate)


class YahooFxRateUpdateStrategy(FxRateUpdateStrategy):
    def _get_fx_rates_from_source(
        self,
        currency_code_list: List[str],
        value_date: timezone.datetime,
    ) -> Dict[str, float]:
        fx_rates = {}
        for ccy in currency_code_list:
            pair_code = f"{ccy}EUR=X"
            data = yf.Ticker(pair_code)
            date_str = value_date.strftime("%Y-%m-%d")
            hist = data.history(
                start=date_str,
                end=(value_date + timezone.timedelta(days=1)).strftime("%Y-%m-%d"),
            )
            fx_rates[ccy] = hist["Close"].iloc[-1]
        return fx_rates

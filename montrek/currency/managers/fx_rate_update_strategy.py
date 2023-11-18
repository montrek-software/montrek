from typing import List, Dict

class FxRateUpdateStrategy:
    def update_fx_rates(self):
        currency_code_list = ["USD", "EUR", "GBP"]
        fx_rates = self._get_fx_rates_from_source(currency_code_list)

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

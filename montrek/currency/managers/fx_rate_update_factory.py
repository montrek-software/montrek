from currency.managers.fx_rate_update_strategy import (
    FxRateUpdateStrategy,
    YahooFxRateUpdateStrategy,
)


class FxRateUpdateFactory:
    @staticmethod
    def get_fx_rate_update_strategy(
        fx_rate_update_strategy: str,
    ) -> FxRateUpdateStrategy:
        if fx_rate_update_strategy.upper() == "YAHOO":
            return YahooFxRateUpdateStrategy()
        else:
            raise ValueError(
                f"Unknown fx rate update strategy for {fx_rate_update_strategy}"
            )

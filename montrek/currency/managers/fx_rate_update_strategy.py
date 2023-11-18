

class FxRateUpdateStrategy:
    def __init__(self):
        self.currencies = []

    def get_all_currencies_from_db(self):
        # Load all currencies currently present in the database
        # and store them in self.currencies
        pass
    def update_fx_rates(self):
        raise NotImplementedError("Subclasses should implement this")

class YahooFxRateUpdateStrategy(FxRateUpdateStrategy):
    def update_fx_rates(self):
        # Code to get fx rates from yahoo and stored them in the database
        pass

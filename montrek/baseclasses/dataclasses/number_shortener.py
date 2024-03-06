from typing import Protocol


class NumberShortenerProtocol(Protocol):
    def shorten(self, number: float, format: str) -> str:
        pass


class NoShortening:
    def shorten(self, number: float, format: str) -> str:
        return f"{{0:{format}}}".format(number)


class BaseShortening:
    order: int = 1
    symbol: str = ""

    def shorten(self, number: float, format: str) -> str:
        return f"{{0:{format}}}{self.symbol}".format(number / 10**self.order)


class KiloShortening(BaseShortening):
    order: int = 3
    symbol: str = "k"


class MillionShortening(BaseShortening):
    order: int = 6
    symbol: str = "mn"


class BillionShortening(BaseShortening):
    order: int = 9
    symbol: str = "bn"

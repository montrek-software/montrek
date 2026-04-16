from abc import abstractmethod

from django.conf import settings

from montrek.utils import SystemFormatting


class NumberShortenerABC:
    def get_format_str(self, decimal_places: int, thousands: str = ",") -> str:
        if thousands in (None, False, ""):
            normalized_thousands = ""
        elif thousands in (",", "_"):
            normalized_thousands = thousands
        else:
            raise ValueError(
                "thousands must be one of ',', '_', or empty to disable grouping"
            )

        return f"{normalized_thousands}.{decimal_places}f"

    def _localize(self, value: str) -> str:
        if (
            getattr(settings, "NUMBER_FORMATTING", SystemFormatting.EN)
            == SystemFormatting.DE
        ):
            return value.replace(",", "X").replace(".", ",").replace("X", ".")
        return value

    @abstractmethod
    def shorten(
        self, number: float, decimal_places: int, thousands: str = ","
    ) -> str: ...  # pragma: no cover


class NoShortening(NumberShortenerABC):
    def shorten(self, number: float, decimal_places: int, thousands: str = ",") -> str:
        fmt = self.get_format_str(decimal_places, thousands)
        return self._localize(f"{number:{fmt}}")


class BaseShortening(NumberShortenerABC):
    order: int = 1
    symbol: str = ""

    def shorten(self, number: float, decimal_places: int, thousands: str = ",") -> str:
        fmt = self.get_format_str(decimal_places, thousands)
        formatted_number = f"{number / 10**self.order:{fmt}}"
        return self._localize(formatted_number) + self.symbol


class KiloShortening(BaseShortening):
    order: int = 3
    symbol: str = "k"


class MillionShortening(BaseShortening):
    order: int = 6
    symbol: str = "mn"


class BillionShortening(BaseShortening):
    order: int = 9
    symbol: str = "bn"

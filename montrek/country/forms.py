from django import forms

from asset.models import AssetStaticSatellite
from asset.models import AssetLiquidSatellite
from asset.models import AssetTimeSeriesSatellite
from currency.models import CurrencyStaticSatellite
from currency.repositories.currency_repository import CurrencyRepository
from baseclasses.forms import MontrekCreateForm


class CountryCreateForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

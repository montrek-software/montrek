from django import forms

from .models import AssetStaticSatellite
from .models import AssetLiquidSatellite

class AssetStaticSatelliteForm(forms.ModelForm):
    class Meta:
        model = AssetStaticSatellite
        fields = ('asset_name', 'asset_type')


class AssetLiquidSatelliteForm(forms.ModelForm):
    class Meta:
        model = AssetLiquidSatellite
        fields = ('asset_isin', 'asset_wkn')

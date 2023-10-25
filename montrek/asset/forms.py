from django import forms

from .models import AssetStaticSatellite

class AssetStaticSatelliteForm(forms.ModelForm):
    class Meta:
        model = AssetStaticSatellite
        fields = ('asset_name', 'asset_type')


from django import forms

from .models import AssetStaticSatellite
from .models import AssetLiquidSatellite
from .models import AssetTimeSeriesSatellite


class AssetTemplateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({"id": f"id_{field}"})


class AssetStaticSatelliteForm(AssetTemplateForm):
    class Meta:
        model = AssetStaticSatellite
        fields = ("asset_name", "asset_type")


class AssetLiquidSatelliteForm(AssetTemplateForm):
    class Meta:
        model = AssetLiquidSatellite
        fields = ("asset_isin", "asset_wkn")


class AssetTimeSeriesSatelliteForm(AssetTemplateForm):
    value_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), required=True
    )
    class Meta:
        model = AssetTimeSeriesSatellite
        fields = ("price", "value_date")

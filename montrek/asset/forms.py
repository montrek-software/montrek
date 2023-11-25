from django import forms

from asset.models import AssetStaticSatellite
from asset.models import AssetLiquidSatellite
from asset.models import AssetTimeSeriesSatellite
from currency.models import CurrencyStaticSatellite


class AssetTemplateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({"id": f"id_{field}"})


class AssetStaticSatelliteForm(AssetTemplateForm):
    asset_ccy = forms.ModelChoiceField(
        queryset=CurrencyStaticSatellite.objects.all(),
        label="Currency",
        to_field_name="ccy_name",
        required=True,
        empty_label="Select Currency"
    )

    class Meta:
        model = AssetStaticSatellite
        fields = ("asset_name", "asset_type", "asset_ccy")


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

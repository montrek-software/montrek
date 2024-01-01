from django import forms

from asset.models import AssetStaticSatellite
from asset.models import AssetLiquidSatellite
from asset.models import AssetTimeSeriesSatellite
from currency.models import CurrencyStaticSatellite
from baseclasses.forms import MontrekCreateForm
from currency.repositories.currency_repository import CurrencyRepository

class AssetCreateForm(MontrekCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_link_choice_field(
            display_field="ccy_code",
            link_name="link_asset_currency",
            queryset=CurrencyRepository().std_queryset(),
        )
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

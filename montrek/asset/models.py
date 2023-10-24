from django.db import models
from baseclasses import models as baseclass_models
from asset.managers.validators import montrek_isin_validator
from asset.managers.validators import montrek_wkn_validator

# Create your models here.

class AssetHub(baseclass_models.MontrekHubABC): pass

class AssetStaticSatellite(baseclass_models.MontrekSatelliteABC): 
    hub_entity = models.ForeignKey(AssetHub, on_delete=models.CASCADE, related_name="static_satellites")
    identifier_fields = ['asset_name']
    asset_name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=100)

class AssetLiquidSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(AssetHub, on_delete=models.CASCADE, related_name="liquid_satellites")
    identifier_fields = ["asset_isin", "asset_wkn"]
    asset_isin = models.CharField(max_length=12,validators=[montrek_isin_validator])
    asset_wkn = models.CharField(max_length=6, validators=[montrek_wkn_validator])

class AssetTimeSeriesSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(AssetHub, on_delete=models.CASCADE, related_name="time_series_satellites")
    price = models.DecimalField(max_digits=10, decimal_places=2)

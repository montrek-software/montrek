from django.db import models
from baseclasses import models as baseclass_models

# Create your models here.

class AssetHub(baseclass_models.MontrekHubABC): pass

class AssetStaticSatellite(baseclass_models.MontrekSatelliteABC): 
    hub_entity = models.ForeignKey(AssetHub, on_delete=models.CASCADE, related_name="static_satellites")
    identifier_fields = ["isin", "wkn"]
    name = models.CharField(max_length=100)
    #TODO ISIN Validator
    isin = models.CharField(max_length=100)
    wkn = models.CharField(max_length=100)
    #TODO Add asset Type
    asset_type = models.CharField(max_length=100)


class AssetTimeSeriesSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(AssetHub, on_delete=models.CASCADE, related_name="time_series_satellites")
    price = models.DecimalField(max_digits=10, decimal_places=2)

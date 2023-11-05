from django.db import models
from django.utils import timezone
from baseclasses import models as baseclass_models

# Create your models here.


class CurrencyHub(baseclass_models.MontrekHubABC):
    pass


class CurrencyStaticSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(CurrencyHub, on_delete=models.CASCADE)
    ccy_name = models.CharField(max_length=30)
    ccy_code = models.CharField(max_length=3)
    identifier_fields = ["ccy_code"]


class CurrencyTimeSeriesSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(CurrencyHub, on_delete=models.CASCADE)
    value_date = models.DateField(default=timezone.now)
    fx_rate = models.DecimalField(max_digits=10, decimal_places=4, default=0.0)
    identifier_fields = ["value_date", "hub_entity"]

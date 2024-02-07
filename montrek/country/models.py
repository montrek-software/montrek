from django.db import models
from baseclasses import models as baseclass_models

# Create your models here.


class CountryHub(baseclass_models.MontrekHubABC):
    pass


class CountryStaticSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(CountryHub, on_delete=models.CASCADE)
    country_name = models.CharField(max_length=255)
    country_code = models.CharField(max_length=3)
    identifier_fields = ["country_code"]

    def __str__(self):
        return self.country_name

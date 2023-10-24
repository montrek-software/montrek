from django.db import models
from baseclasses import models as baseclass_models

# Create your models here.

class DepotHub(baseclass_models.MontrekHubABC):
    pass

class DepotSatelitte(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(DepotHub, on_delete=models.CASCADE)
    depot_name = models.CharField(max_length=200)
    identifier_fields = ['depot_name']

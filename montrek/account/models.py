from django.db import models
from baseclasses import models as baseclass_models

# Create your models here.

class AccountHub(baseclass_models.MontrekHubABC): pass


class AccountStaticSatellite(baseclass_models.MontrekSatelliteABC):
    account_name = models.CharField(max_length=50) 
    hub_entity = models.ForeignKey(AccountHub, on_delete=models.CASCADE)

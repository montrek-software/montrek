from django.db import models
from baseclasses import models as baseclass_models

# Create your models here.

class CreditInstitutionHub(baseclass_models.MontrekHubABC): pass

class CreditInstitutionStaticSatellite(baseclass_models.MontrekSatelliteABC): 
    hub_entity = models.ForeignKey(CreditInstitutionHub, on_delete=models.CASCADE)

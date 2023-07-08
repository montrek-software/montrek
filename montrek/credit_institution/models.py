from django.db import models
from baseclasses import models as baseclass_models

# Create your models here.

class CreditInstitutionHub(baseclass_models.MontrekHubABC): pass

class CreditInstitutionStaticSatellite(baseclass_models.MontrekSatelliteABC): 
    class UploadMethod(models.TextChoices):
        NONE = "none"
        DKB = "dkb"
    hub_entity = models.ForeignKey(CreditInstitutionHub, on_delete=models.CASCADE)
    identifier_fields = ['credit_institution_name', 'credit_institution_bic']
    credit_institution_name = models.CharField(max_length=255, default='NoName')
    credit_institution_bic= models.CharField(max_length=11, default='NoBic')
    account_upload_method = models.CharField(max_length=5, choices=UploadMethod.choices, default=UploadMethod.NONE)

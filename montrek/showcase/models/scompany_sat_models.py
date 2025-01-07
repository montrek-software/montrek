from django.db import models

from baseclasses.models import MontrekSatelliteABC
from showcase.models.scompany_hub_models import SCompanyHub


class SCompanyStaticSatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(SCompanyHub, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_sector = models.CharField(max_length=255, blank=True, null=True)

    identifier_fields = ["company_name"]

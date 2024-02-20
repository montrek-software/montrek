from django.db import models
from baseclasses import models as baseclass_models


class CompanyHub(baseclass_models.MontrekHubABC):
    pass


class CompanyStaticSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(CompanyHub, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    bloomberg_ticker = models.CharField(max_length=20)
    identifier_fields = ["bloomberg_ticker"]

    def __str__(self):
        return self.bloomberg_ticker

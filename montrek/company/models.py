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


class CompanyTimeSeriesSatellite(baseclass_models.MontrekTimeSeriesSatelliteABC):
    hub_entity = models.ForeignKey(
        CompanyHub, on_delete=models.CASCADE, related_name="asset_time_series_satellite"
    )
    identifier_fields = ["value_date", "hub_entity_id"]
    total_revenue = models.DecimalField(max_digits=20, decimal_places=2)
    value_date = models.DateField()

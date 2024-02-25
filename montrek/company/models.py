from django.db import models
from baseclasses import models as baseclass_models


class CompanyHub(baseclass_models.MontrekHubABC):
    link_company_file_upload_registry = models.ManyToManyField(
        "file_upload.FileUploadRegistryHub",
        related_name="link_file_upload_registry_company",
        through="LinkCompanyFileUploadRegistry",
    )


class CompanyStaticSatellite(baseclass_models.MontrekSatelliteABC):
    hub_entity = models.ForeignKey(CompanyHub, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    bloomberg_ticker = models.CharField(max_length=20)
    effectual_identifier = models.CharField(max_length=255)
    identifier_fields = ["effectual_identifier"]

    def __str__(self):
        return self.effectual_identifier


class CompanyTimeSeriesSatellite(baseclass_models.MontrekTimeSeriesSatelliteABC):
    hub_entity = models.ForeignKey(
        CompanyHub, on_delete=models.CASCADE, related_name="asset_time_series_satellite"
    )
    identifier_fields = ["value_date", "hub_entity_id"]
    total_revenue = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    value_date = models.DateField()


class LinkCompanyFileUploadRegistry(baseclass_models.MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey("company.CompanyHub", on_delete=models.CASCADE)
    hub_out = models.ForeignKey(
        "file_upload.FileUploadRegistryHub", on_delete=models.CASCADE
    )

from django.db import models

from baseclasses.models import MontrekSatelliteABC
from baseclasses.utils import ChoicesEnum
from info.models.download_registry_hub_models import DownloadRegistryHub


class DOWNLOAD_TYPES(ChoicesEnum):
    XLSX = "xlsx"
    CSV = "csv"
    API = "api"
    PDF = "pdf"


class DownloadRegistrySatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(DownloadRegistryHub, on_delete=models.CASCADE)

    download_name = models.CharField()
    dowload_type = models.CharField(max_length=25, choices=DOWNLOAD_TYPES.to_list())

    identifier_fields = ["hub_entity_id"]

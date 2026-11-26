from django.db import models

from baseclasses.models import MontrekSatelliteABC
from baseclasses.dataclasses.download_type import DownloadType
from info.models.download_registry_hub_models import DownloadRegistryHub

__all__ = ["DownloadRegistrySatellite", "DownloadType"]


class DownloadRegistrySatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(DownloadRegistryHub, on_delete=models.CASCADE)

    download_name = models.CharField()
    download_type = models.CharField(max_length=25, choices=DownloadType.to_list())

    identifier_fields = ["hub_entity_id"]

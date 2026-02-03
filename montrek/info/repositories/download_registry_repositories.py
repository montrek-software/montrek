from baseclasses.repositories.montrek_repository import MontrekRepository
from info.models.download_registry_hub_models import DownloadRegistryHub
from info.models.download_registry_sat_models import (
    DownloadRegistrySatellite,
)


class DownloadRegistryRepository(MontrekRepository):
    hub_class = DownloadRegistryHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            DownloadRegistrySatellite, ["download_name", "download_type"]
        )

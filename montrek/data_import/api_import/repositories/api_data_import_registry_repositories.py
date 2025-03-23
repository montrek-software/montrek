from data_import.base.repositories.registry_repositories import RegistryRepositoryABC
from data_import.api_import.models.api_registry_sat_models import (
    ApiRegistrySatellite,
    ApiRegistryHub,
)


class ApiDataImportRegistryRepository(RegistryRepositoryABC):
    registry_satellite = ApiRegistrySatellite
    hub_class = ApiRegistryHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            self.registry_satellite,
            [
                "import_url",
            ],
        )
        return super().set_annotations()

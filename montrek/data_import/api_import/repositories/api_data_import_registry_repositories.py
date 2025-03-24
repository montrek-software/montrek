from data_import.base.repositories.registry_repositories import RegistryRepositoryABC
from data_import.api_import.models import (
    ApiRegistrySatellite,
)


class ApiDataImportRegistryRepository(RegistryRepositoryABC):
    registry_satellite = ApiRegistrySatellite

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            self.registry_satellite,
            [
                "import_url",
            ],
        )
        return super().set_annotations()

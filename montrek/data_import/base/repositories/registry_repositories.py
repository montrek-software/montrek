from baseclasses.repositories.montrek_repository import MontrekRepository
from data_import.base.models.import_registry_base_models import (
    DataImportRegistryBaseSatelliteABC,
)


class RegistryRepositoryABC(MontrekRepository):
    registry_satellite: type[DataImportRegistryBaseSatelliteABC]

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            self.registry_satellite,
            [
                "import_status",
                "import_message",
                "created_at",
            ],
        )

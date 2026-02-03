from baseclasses.managers.montrek_manager import MontrekManager
from info.models.download_registry_sat_models import DOWNLOAD_TYPES
from info.repositories.download_registry_repositories import DownloadRegistryRepository


class DownloadRegistryStorageManager(MontrekManager):
    repository_class = DownloadRegistryRepository

    def store_in_download_registry(
        self, identifier: str, download_type: DOWNLOAD_TYPES
    ):
        self.repository.create_by_dict(
            {"download_name": identifier, "download_type": download_type.value}
        )

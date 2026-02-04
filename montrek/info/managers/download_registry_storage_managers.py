from baseclasses.managers.montrek_manager import MontrekManager
from info.models.download_registry_sat_models import DownloadType
from info.repositories.download_registry_repositories import DownloadRegistryRepository


class DownloadRegistryStorageManager(MontrekManager):
    repository_class = DownloadRegistryRepository

    def store_in_download_registry(self, identifier: str, download_type: DownloadType):
        self.repository.create_by_dict(
            {"download_name": identifier, "download_type": download_type.value}
        )

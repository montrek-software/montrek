from baseclasses.repositories.montrek_repository import MontrekRepository
from download_registry.models.download_registry_hub_models import DownloadRegistryHub


class DownloadRegistryRepository(MontrekRepository):
    hub_class = DownloadRegistryHub

    def set_annotations(self):
        pass

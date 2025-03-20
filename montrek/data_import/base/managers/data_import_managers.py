from typing import Any

from baseclasses.managers.montrek_manager import MontrekManager
from data_import.base.managers.processor_base import ProcessorBaseABC
from data_import.base.repositories.registry_repositories import RegistryRepositoryABC
from data_import.types import ImportDataType


class DataImportManagerABC(MontrekManager):
    registry_repository_class: None | type[RegistryRepositoryABC] = None
    processor_class: None | type[ProcessorBaseABC] = None

    def __init__(self, session_data: dict[str, Any]):
        super().__init__(session_data)
        self.registry_repository: RegistryRepositoryABC = (
            self._get_registry_repository()
        )
        self.registry_hub_pk: int = self._init_registry_and_get_pk()

    def process_import_data(self, import_data: ImportDataType):
        self._update_registry(status="in_progress", message="Data Import in progress")
        processor = self._get_processor(import_data)
        if not processor.pre_check():
            self._update_registry(status="failed", message=processor.get_message())
            return
        processor.process()
        if not processor.post_check():
            self._update_registry(status="failed", message=processor.get_message())
            return
        self._update_registry(status="processed", message=processor.get_message())

    def get_registry(self):
        return self.registry_repository.receive().get(pk=self.registry_hub_pk)

    def _get_registry_repository(self) -> RegistryRepositoryABC:
        if not self.registry_repository_class:
            raise NotImplementedError(
                f"Set 'registry_repository_class' attribute in {self.__class__.__name__}"
            )
        return self.registry_repository_class(self.session_data)

    def _get_processor(self, import_data: ImportDataType) -> ProcessorBaseABC:
        if not self.processor_class:
            raise NotImplementedError(
                f"Set 'processor_class' attribute in {self.__class__.__name__}"
            )
        return self.processor_class(self.session_data, import_data)

    def _init_registry_and_get_pk(self) -> int:
        init_data = {"import_message": "Initialize Import"}
        return self.registry_repository.create_by_dict(init_data).pk

    def _update_registry(self, status: str, message: str):
        update_data = {
            "import_status": status,
            "import_message": message,
            "hub_entity_id": self.registry_hub_pk,
        }
        self.registry_repository.create_by_dict(update_data)

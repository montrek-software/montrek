from typing import Any
from baseclasses.managers.montrek_manager import MontrekManager
from data_import.base.repositories.registry_repositories import RegistryRepositoryABC

ImportDataType = dict[str, Any]


class DataImportManagerABC(MontrekManager):
    registry_repository_class: None | type[RegistryRepositoryABC] = None

    def __init__(self, session_data: dict[str, Any]):
        super().__init__(session_data)
        self.import_data: None | ImportDataType = None
        self.registry_repository: RegistryRepositoryABC = (
            self._get_registry_repository()
        )
        self.registry_pk: int = self._init_registry_and_get_pk()

    def set_import_data(self, import_data: ImportDataType):
        raise NotImplementedError(
            f"Implement 'set_import_data' method in {self.__class__.__name__}"
        )

    def get_registry(self):
        return self.registry_repository.receive().get(pk=self.registry_pk)

    def _get_registry_repository(self) -> RegistryRepositoryABC:
        if not self.registry_repository_class:
            raise NotImplementedError(
                f"Set 'registry_repository' attribute in {self.__class__.__name__}"
            )
        return self.registry_repository_class(self.session_data)

    def _init_registry_and_get_pk(self) -> int:
        init_data = {"import_message": "Initialize Import"}
        return self.registry_repository.create_by_dict(init_data).pk

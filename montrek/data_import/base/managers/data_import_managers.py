from typing import Any

from data_import.base.managers.processor_base import ProcessorBaseABC
from data_import.base.repositories.registry_repositories import RegistryRepositoryABC
from data_import.types import ImportDataType
from process_pipeline.managers.montrek_pipeline_managers import (
    MontrekPipelineManagerABC,
)


class DataImportManagerABC(MontrekPipelineManagerABC):
    registry_repository_class: type[RegistryRepositoryABC]
    processor_class: type[ProcessorBaseABC]
    status_field_name = "import_status"
    message_field_name = "import_message"
    do_process_async = False

    # ---- public entry point ----

    def process_import_data(self, import_data: ImportDataType | None = None) -> bool:
        if import_data is None:
            import_data = {}
        return self.trigger_pipeline(pipeline_data={"import_data": import_data})

    # ---- required overrides ----

    def _init_registry(self, **kwargs) -> int:
        init_data = {
            self.status_field_name: "pending",
            self.message_field_name: "Initialize Import",
        }
        init_data.update(self.additional_registry_data())
        return self.registry_repository.create_by_dict(init_data).pk

    def _build_processor(self, pipeline_data: dict[str, Any]) -> ProcessorBaseABC:
        return self.processor_class(
            self.session_data,
            pipeline_data.get("import_data", {}),
        )

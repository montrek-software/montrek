from typing import Any

from process_pipeline.managers.montrek_pipeline_managers import (
    MontrekPipelineManagerABC,
)
from process_pipeline.tasks.montrek_pipeline_task import MontrekPipelineTask

from file_export.managers.file_export_processor_abc import FileExportProcessorABC
from file_export.repositories.file_export_registry_repository import (
    FileExportRegistryRepositoryABC,
)
from file_export.tasks.file_export_task import FileExportTask


class FileExportManagerABC(MontrekPipelineManagerABC):
    processor_class: type[FileExportProcessorABC]
    registry_repository_class: type[FileExportRegistryRepositoryABC]
    pipeline_task_class: type[MontrekPipelineTask] = FileExportTask
    status_field_name = "export_status"
    message_field_name = "export_message"
    do_process_async = False

    def trigger_export(self, pipeline_data: dict[str, Any] | None = None) -> bool:
        """Run the export, optionally parameterised by what the user picked."""
        return self.trigger_pipeline(pipeline_data=pipeline_data)

    def _init_registry(self, **kwargs) -> int:
        init_data = {
            self.status_field_name: "pending",
            self.message_field_name: "Export is pending",
        }
        init_data.update(self.additional_registry_data())
        return self.registry_repository.create_by_dict(init_data).pk

    def _build_processor(self, pipeline_data: dict[str, Any]) -> FileExportProcessorABC:
        return self.processor_class(self.registry, self.session_data)

    def _on_pipeline_success(self) -> None:
        if self.processor.result_file is not None:
            self._update_registry(export_file=self.processor.result_file)

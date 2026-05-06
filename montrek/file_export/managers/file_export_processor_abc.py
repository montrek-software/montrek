from typing import Any

from django.core.files import File

from process_pipeline.managers.process_pipeline_processor_abc import (
    PipelineProcessorABC,
)


class FileExportProcessorABC(PipelineProcessorABC):
    _result_file: File | None = None

    def __init__(self, registry_hub: Any, session_data: dict[str, Any]) -> None:
        self.registry_hub = registry_hub
        self.session_data = session_data

    @property
    def result_file(self) -> File | None:
        return self._result_file

    def set_result_file(self, file: File) -> None:
        self._result_file = file

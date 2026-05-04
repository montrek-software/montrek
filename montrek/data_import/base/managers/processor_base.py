from typing import Any
from data_import.types import ImportDataType
from process_pipeline.managers.process_pipeline_processor_abc import (
    PipelineProcessorABC,
)


class ProcessorBaseABC(PipelineProcessorABC):
    def __init__(self, session_data: dict[str, Any], import_data: ImportDataType):
        self.session_data = session_data
        self.import_data = import_data

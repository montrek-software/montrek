import os
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files import File
from file_upload.managers.file_upload_registry_manager import FileUploadRegistryManager
from file_upload.models import FileUploadRegistryHubABC
from file_upload.repositories.file_upload_file_repository import (
    FileUploadFileRepository,
)
from file_upload.tasks.file_upload_task import FileUploadTask
from montrek.celery_app import PARALLEL_QUEUE_NAME
from process_pipeline.managers.montrek_pipeline_managers import (
    MontrekPipelineManagerABC,
)
from process_pipeline.managers.process_pipeline_processor_abc import (
    PipelineProcessorABC,
)


class FileUploadProcessorProtocol(PipelineProcessorABC):
    def __init__(
        self,
        file_upload_registry_hub: FileUploadRegistryHubABC,
        session_data: dict[str, Any],
        **kwargs,
    ): ...


class FileUploadManagerABC(MontrekPipelineManagerABC):
    # ---- file storage (actual uploaded bytes) ----
    repository_class: type[FileUploadFileRepository] = FileUploadFileRepository

    # ---- registry display manager (used by views) ----
    file_registry_manager_class: type[FileUploadRegistryManager] = (
        FileUploadRegistryManager
    )

    # ---- pipeline config ----
    processor_class: type[FileUploadProcessorProtocol]
    file_upload_processor_class: type[FileUploadProcessorProtocol]
    do_process_file_async: bool
    pipeline_task_class: type[FileUploadTask] = FileUploadTask
    registry_repository_class = FileUploadRegistryManager.repository_class
    status_field_name = "upload_status"
    message_field_name = "upload_message"
    registry_session_key = "file_upload_registry_id"

    def __init_subclass__(cls, task_queue: str = PARALLEL_QUEUE_NAME, **kwargs):
        # Migrate old class attribute namings to new ones
        if hasattr(cls, "file_registry_manager_class"):
            cls.registry_repository_class = (
                cls.file_registry_manager_class.repository_class
            )
        if hasattr(cls, "file_upload_processor_class"):
            cls.processor_class = cls.file_upload_processor_class
        if hasattr(cls, "do_process_file_async"):
            cls.do_process_async = cls.do_process_file_async
        super().__init_subclass__(task_queue, **kwargs)

    def __init__(self, session_data: dict[str, Any]) -> None:
        super().__init__(session_data=session_data)
        self.file_path = ""

    # ---- public entry point ----

    def upload_and_process(self, file: File) -> bool:
        return self.trigger_pipeline(file=file)

    # ---- pipeline hooks ----

    def _init_registry(self, file: File, **kwargs) -> int:
        file_name = Path(file.name).name
        return self.registry_repository.std_create_object(
            {
                "file_name": file_name,
                "file_type": file_name.split(".")[-1],
                self.status_field_name: "pending",
                self.message_field_name: "Upload is pending",
                "link_file_upload_registry_file_upload_file": self._get_upload_file_hub(
                    file
                ),
                "celery_task_id": "",
            }
        ).pk

    def _build_processor(self, pipeline_data: dict[str, Any]) -> PipelineProcessorABC:
        self.file_path = os.path.join(settings.MEDIA_ROOT, self.registry.file)
        return self.processor_class(self.registry, self.session_data)

    def _apply_step(self, step: str) -> bool:
        # Existing processors pass file_path to each step.
        # Remove once all processors are migrated to no-argument steps.
        if not getattr(self.processor, step)(self.file_path):
            self._set_status("failed", self.processor.message)
            return False
        return True

    # ---- helpers ----

    def _get_upload_file_hub(self, file: File):
        return self.repository.std_create_object({"file": file})

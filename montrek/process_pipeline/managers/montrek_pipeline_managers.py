from typing import Any
from baseclasses.managers.montrek_manager import MontrekManager

from process_pipeline.managers.process_pipeline_processor_abc import (
    PipelineProcessorABC,
)
from montrek.celery_app import (
    PARALLEL_QUEUE_NAME,
)
from process_pipeline.repositories.pipeline_registry_repositories import (
    PipelineRegistryRepositoryABC,
)
from process_pipeline.tasks.montrek_pipeline_task import MontrekPipelineTask


TASK_SCHEDULED_MESSAGE = (
    "Successfully scheduled background task for processing. "
    "You will receive an email once the task has finished."
)


class MontrekPipelineManagerABC(MontrekManager):
    # ---- required: subclass must set ----
    processor_class: type[PipelineProcessorABC]
    registry_repository_class: type[PipelineRegistryRepositoryABC]
    pipeline_task_class: type[MontrekPipelineTask]
    status_field_name: str  # "upload_status" / "import_status" / "process_status"
    message_field_name: str  # "upload_message" / "import_message" / "process_message"

    # ---- configuration ----
    do_process_async: bool = True
    registry_session_key: str = "pipeline_registry_id"

    # ---- set by __init_subclass__ ----
    pipeline_task: MontrekPipelineTask

    def __init_subclass__(cls, task_queue: str = PARALLEL_QUEUE_NAME, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.do_process_async and hasattr(cls, "pipeline_task_class"):
            cls.pipeline_task = cls.pipeline_task_class(
                manager_class=cls, queue=task_queue
            )

    def __init__(self, session_data: dict[str, Any]) -> None:
        super().__init__(session_data=session_data)
        self.registry_repository = self.registry_repository_class(session_data)
        self.registry: Any = None
        self.processor: PipelineProcessorABC | None = None
        self.message: str = ""

    # ---- public entry point (called from view or directly) ----

    def trigger_pipeline(
        self, pipeline_data: dict[str, Any] | None = None, **kwargs
    ) -> bool:
        if pipeline_data is None:
            pipeline_data = {}
        self.processor = self._build_processor(pipeline_data)
        self.create_registry(**kwargs)
        if self.do_process_async:
            task_result = self.pipeline_task.delay(
                session_data=self.session_data,
                pipeline_data=pipeline_data,
            )
            self._load_registry()
            self._update_registry(celery_task_id=task_result.id)
            self.message = TASK_SCHEDULED_MESSAGE
            return True
        return self.process(pipeline_data=pipeline_data)

    def create_registry(self, **kwargs):
        self.session_data[self.registry_session_key] = self._init_registry(**kwargs)

    # ---- called by Celery task ----

    def process(self, pipeline_data: dict[str, Any] | None = None) -> bool:
        if pipeline_data is None:
            pipeline_data = {}
        self._load_registry()
        self._update_registry(
            **{
                self.status_field_name: "in_progress",
                self.message_field_name: "Processing in progress",
            }
        )
        if not self._apply_step("pre_check"):
            return False
        if not self._apply_step("process"):
            return False
        if not self._apply_step("post_check"):
            return False
        self._on_pipeline_success()
        self._set_status("processed", self.processor.message)
        return True

    def send_mail(self) -> bool:
        return self.processor.send_mail

    def get_registry(self) -> Any:
        return self.registry

    def get_message(self) -> str:
        return self.message

    # ---- internal ----

    def _apply_step(self, step: str) -> bool:
        if not getattr(self.processor, step)():
            self._set_status("failed", self.processor.message)
            return False
        return True

    def _set_status(self, status: str, message: str = "") -> None:
        self._update_registry(
            **{
                self.status_field_name: status,
                self.message_field_name: message,
            }
        )
        self.message = self.processor.message

    # ---- default implementations (may override if repo interface differs) ----

    def _load_registry(self) -> None:
        pk = self.session_data[self.registry_session_key]
        self.registry = self.registry_repository.receive(apply_filter=False).get(
            hub__pk=pk
        )

    def _update_registry(self, **kwargs) -> None:
        att_dict = self.registry_repository.object_to_dict(self.registry)
        att_dict.update(kwargs)
        att_dict.update(self.additional_registry_data())
        registry_hub = self.registry_repository.std_create_object(att_dict)
        self.registry = self.registry_repository.receive(apply_filter=False).get(
            hub__pk=registry_hub.pk
        )

    def additional_registry_data(self) -> dict:
        return {}

    # ---- must override ----

    def _init_registry(self, **kwargs) -> int:
        raise NotImplementedError(
            f"Implement _init_registry in {self.__class__.__name__}"
        )

    def _build_processor(self, pipeline_data: dict[str, Any]) -> PipelineProcessorABC:
        raise NotImplementedError(
            f"Implement _build_processor in {self.__class__.__name__}"
        )

    # ---- optional hook ----

    def _on_pipeline_success(self) -> None:
        pass

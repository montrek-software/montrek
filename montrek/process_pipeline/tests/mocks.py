from unittest.mock import MagicMock

from process_pipeline.managers.montrek_pipeline_managers import (
    MontrekPipelineManagerABC,
)
from process_pipeline.managers.process_pipeline_processor_abc import (
    PipelineProcessorABC,
)

SESSION_DATA = {"user_id": 1}


# ---- processors ----


class MockProcessor(PipelineProcessorABC):
    def pre_check(self) -> bool:
        self.set_message("pre_check ok")
        return True

    def process(self) -> bool:
        self.set_message("process ok")
        return True

    def post_check(self) -> bool:
        self.set_message("post_check ok")
        return True


class MockProcessorFailPreCheck(MockProcessor):
    def pre_check(self) -> bool:
        self.set_message("Pre Check Failed")
        return False


class MockProcessorFailProcess(MockProcessor):
    def process(self) -> bool:
        self.set_message("Process Failed")
        return False


class MockProcessorFailPostCheck(MockProcessor):
    def post_check(self) -> bool:
        self.set_message("Post Check Failed")
        return False


class MockProcessorNoMail(MockProcessor):
    send_mail = False


# ---- managers ----
# ConcreteTestManager avoids all DB operations so pipeline logic can be unit-tested
# without models or migrations.


class ConcreteTestManager(MontrekPipelineManagerABC):
    status_field_name = "process_status"
    message_field_name = "process_message"
    do_process_async = False
    registry_repository_class = MagicMock  # satisfies __init__ without a real repo
    processor_class = MockProcessor

    def __init__(self, session_data):
        super().__init__(session_data)
        self._registry_updates: list[dict] = []

    def _init_registry(self, **kwargs) -> int:
        return 1

    def _load_registry(self) -> None:
        self.registry = MagicMock(pk=1)

    def _update_registry(self, **kwargs) -> None:
        self._registry_updates.append(dict(kwargs))

    def _build_processor(self, pipeline_data) -> PipelineProcessorABC:
        return self.processor_class()


class ConcreteTestManagerFailPreCheck(ConcreteTestManager):
    processor_class = MockProcessorFailPreCheck


class ConcreteTestManagerFailProcess(ConcreteTestManager):
    processor_class = MockProcessorFailProcess


class ConcreteTestManagerFailPostCheck(ConcreteTestManager):
    processor_class = MockProcessorFailPostCheck


class ConcreteTestManagerNoMail(ConcreteTestManager):
    processor_class = MockProcessorNoMail

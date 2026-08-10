from typing import Any


class PipelineProcessorABC:
    send_mail: bool = True
    _message: str = ""

    @property
    def message(self) -> str:
        return self._message

    def set_message(self, message: str) -> None:
        self._message = message

    @property
    def pipeline_data(self) -> dict[str, Any]:
        """What the user chose when triggering the pipeline.

        Set by the manager after the processor is built, so a processor never has
        to reach back into the request or the URLconf to find out what it should
        do. Travels through Celery as JSON, so it holds plain data only.
        """
        return getattr(self, "_pipeline_data", {})

    def set_pipeline_data(self, pipeline_data: dict[str, Any]) -> None:
        self._pipeline_data = dict(pipeline_data)

    def pre_check(self) -> bool:
        raise NotImplementedError(f"Implement pre_check in {self.__class__.__name__}")

    def process(self) -> bool:
        raise NotImplementedError(f"Implement process in {self.__class__.__name__}")

    def post_check(self) -> bool:
        raise NotImplementedError(f"Implement post_check in {self.__class__.__name__}")

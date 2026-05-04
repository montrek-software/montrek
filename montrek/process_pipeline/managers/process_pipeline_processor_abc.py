class PipelineProcessorABC:
    send_mail: bool = True
    _message: str = ""

    @property
    def message(self) -> str:
        return self._message

    def set_message(self, message: str) -> None:
        self._message = message

    def pre_check(self) -> bool:
        raise NotImplementedError(f"Implement pre_check in {self.__class__.__name__}")

    def process(self) -> bool:
        raise NotImplementedError(f"Implement process in {self.__class__.__name__}")

    def post_check(self) -> bool:
        raise NotImplementedError(f"Implement post_check in {self.__class__.__name__}")

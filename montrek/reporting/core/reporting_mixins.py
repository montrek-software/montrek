class ReportingChecksMixin:
    def _check_for_generating(self) -> None:
        if self.text is None:
            raise ValueError("Text is not generated, call generate() first")

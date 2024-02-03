from account.managers.not_implemented_processor import NotImplementedFileUploadProcessor


class OnvistaFileUploadProcessor:
    message = "Not implemented"

    def __init__(self, account_hub):
        self.account_hub = account_hub
        self.subprocessor = NotImplementedFileUploadProcessor()

    def pre_check(self, file_path: str) -> bool:
        self._get_subprocessor(file_path)
        return self.subprocessor.pre_check(file_path)

    def _get_subprocessor(self, file_path: str):
        index_tag = open(file_path).readline().strip()
        if index_tag.startswith("Depotuebersicht"):
            self.subprocessor = OnvistaFileUploadDepotProcessor()
            return
        self.subprocessor = NotImplementedFileUploadProcessor()
        self.message = "File cannot be processed"


class OnvistaFileUploadDepotProcessor:
    message = "Not implemented"

    def pre_check(self, file_path: str) -> bool:
        return True

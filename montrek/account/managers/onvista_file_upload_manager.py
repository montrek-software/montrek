from account.managers.not_implemented_file_upload_manager import NotImplementedFileUploadProcessor
class OnvistaFileUploadProcessor:
    message = "Not implemented"
    def __init__(self, account_hub):
        self.account_hub = account_hub
        self.subprocessor = NotImplementedFileUploadProcessor()

    def pre_check(self, file_path: str):
        self._get_subprocessor(file_path)
        return self.subprocessor.pre_check(file_path)

class OnvistaFileUploadDepotProcessor:
    message = "Not implemented"

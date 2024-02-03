from account.managers.dkb_file_upload_manager import DkbFileUploadProcessor
from account.managers.onvista_file_upload_manager import OnvistaFileUploadProcessor
from account.managers.not_implemented_file_upload_manager import (
    NotImplementedFileUploadProcessor,
)
from account.repositories.account_repository import AccountRepository


class AccountFileUploadProcessor:
    message = "Not implemented"

    def __init__(self, **kwargs):
        account_hub = AccountRepository().std_queryset().get(pk=kwargs["pk"])
        match account_hub.account_upload_method:
            case "dkb":
                self.sub_processor = DkbFileUploadProcessor(account_hub)
            case "onvis":
                self.sub_processor = OnvistaFileUploadProcessor(account_hub)
            case _:
                self.sub_processor = NotImplementedFileUploadProcessor()
                self.sub_processor.message = f"Account upload method {account_hub.account_upload_method} not implemented"

    def process(self, file_path: str, file_upload_registry_hub):
        result = self.sub_processor.process(file_path, file_upload_registry_hub)
        self.message = self.sub_processor.message
        return result

    def pre_check(self, file_path: str):
        result = self.sub_processor.pre_check(file_path)
        self.message = self.sub_processor.message
        return result

    def post_check(self, file_path: str):
        result = self.sub_processor.post_check(file_path)
        self.message = self.sub_processor.message
        return result

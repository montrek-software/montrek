from typing import Any
from account.managers.dkb_file_upload_manager import DkbFileUploadProcessor
from account.managers.onvista_file_upload_manager import OnvistaFileUploadProcessor
from account.managers.not_implemented_processor import (
    NotImplementedFileUploadProcessor,
)
from account.repositories.account_repository import AccountRepository
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)


class AccountFileUploadProcessor:
    message = "Not implemented"
    file_upload_registry = None

    def __init__(
        self, file_upload_registry_id: int, session_data: dict[str, Any], **kwargs
    ):
        account_hub_id = kwargs.get("pk")
        account_hub = self._set_registry_to_account(
            account_hub_id, file_upload_registry_id
        )
        match account_hub.account_upload_method:
            case "dkb":
                self.sub_processor = DkbFileUploadProcessor(account_hub, session_data)
            case "onvis":
                self.sub_processor = OnvistaFileUploadProcessor(
                    account_hub, session_data
                )
            case _:
                self.sub_processor = NotImplementedFileUploadProcessor()
                self.sub_processor.message = f"Account upload method {account_hub.account_upload_method} not implemented"

    def process(self, file_path: str):
        result = self.sub_processor.process(file_path)
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

    def _set_registry_to_account(
        self, account_hub_id: int, file_upload_registry_id: int
    ):
        file_upload_registry_hub = (
            FileUploadRegistryRepository()
            .std_queryset()
            .get(pk=file_upload_registry_id)
        )
        account_hub = AccountRepository().std_queryset().get(pk=account_hub_id)
        account_hub.link_account_file_upload_registry.add(file_upload_registry_hub)
        return account_hub

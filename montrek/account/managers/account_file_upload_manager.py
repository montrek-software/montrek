from account.managers.transaction_upload_methods import upload_dkb_transactions
from account.repositories.account_repository import AccountRepository

class AccountFileUploadProcessor:
    message = "Not implemented"
    def __init__(self, **kwargs):
        account_hub = AccountRepository().std_queryset().get(pk=kwargs["pk"])
        if account_hub.account_upload_method == 'dkb':
            self.sub_processor = DKBFileUploadProcessor(account_hub)

    def process(self, file_path: str, file_upload_registry_hub ):
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

class DKBFileUploadProcessor(AccountFileUploadProcessor):
    def __init__(self, account_hub):
        self.account_hub = account_hub

    def process(self, file_path: str, file_upload_registry_hub ):
        updated_transactions = upload_dkb_transactions(self.account_hub, file_path)
        self.account_hub.link_account_file_upload_registry.add(file_upload_registry_hub)
        self.message = f"DKB upload was successful ({len(updated_transactions)} transactions)"
        return True

    def pre_check(self, file_path: str):
        return True

    def post_check(self, file_path: str):
        return True

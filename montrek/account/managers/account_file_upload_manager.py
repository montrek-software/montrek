from account.managers.transaction_upload_methods import upload_dkb_transactions
from account.repositories.account_repository import AccountRepository

class AccountFileUploadProcessor:
    message = "Not implemented"
    def __init__(self, **kwargs):
        self.account_hub = AccountRepository().std_queryset().get(pk=kwargs["pk"])

    def process(self, file_path: str):
        upload_dkb_transactions(self.account_hub, file_path)
        self.message = "DKB upload was successful"
        return True

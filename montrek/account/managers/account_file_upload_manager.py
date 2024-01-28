from account.managers.transaction_upload_methods import upload_dkb_transactions
from account.repositories.account_repository import AccountRepository

class AccountFileUploadProcessor:
    message = "Not implemented"
    def __init__(self, **kwargs):
        self.account_hub = AccountRepository().std_queryset().get(pk=kwargs["pk"])

    def process(self, file_path: str, file_upload_registry_hub ):
        if self.account_hub.account_upload_method == 'dkb':
            updated_transactions = upload_dkb_transactions(self.account_hub, file_path)
            self.account_hub.link_account_file_upload_registry.add(file_upload_registry_hub)
            self.message = f"DKB upload was successful ({len(updated_transactions)} transactions)"
        return True

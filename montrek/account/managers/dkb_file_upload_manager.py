from typing import Any
from account.managers.transaction_upload_methods import upload_dkb_transactions
from account.repositories.account_repository import AccountRepository
import csv


class DkbFileUploadProcessor:
    message = ""

    def __init__(self, account_hub, session_data: Dict[str, Any]):
        self.session_data = session_data
        self.account_hub = account_hub
        self.meta_data = {}

    def process(self, file_path: str):
        updated_transactions = upload_dkb_transactions(
            self.account_hub, file_path, self.session_data
        )
        self.message = (
            f"DKB upload was successful ({len(updated_transactions)} transactions)"
        )
        self.account_hub = (
            AccountRepository().std_queryset().get(pk=self.account_hub.pk)
        )
        return True

    def pre_check(self, file_path: str):
        self._get_meta_data(file_path)
        if self.meta_data["iban"] != self.account_hub.bank_account_iban:
            self.message = f"IBAN in file ({self.meta_data['iban']}) does not match account iban ({self.account_hub.bank_account_iban})"
            return False
        return True

    def post_check(self, file_path: str):
        self._get_meta_data(file_path)
        account_value = float(self.account_hub.account_value)
        diff_values = account_value - self.meta_data["value"]
        if abs(diff_values) > 0.02:
            self.message = f"Bank account value and value from file differ by {diff_values:,.2f} EUR"
            return False
        return True

    def _get_meta_data(self, file_path: str):
        if self.meta_data:
            return
        with open(file_path, newline="", encoding="iso-8859-1") as csvfile:
            reader = csv.reader(csvfile, delimiter=";", quotechar='"')
            iban = next(reader)[1].split("/")[0].replace(" ", "")
            for _ in range(3):
                next(reader)
            value = (
                next(reader)[1].replace(" EUR", "").replace(".", "").replace(",", ".")
            )
            value = float(value)
            self.meta_data = {
                "iban": iban,
                "value": value,
            }

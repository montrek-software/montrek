import pandas as pd
from account.managers.not_implemented_processor import NotImplementedFileUploadProcessor
from asset.reposotories.asset_repository import AssetRepository


class OnvistaFileUploadProcessor:
    message = "Not implemented"

    def __init__(self, account_hub):
        self.account_hub = account_hub
        self.subprocessor = NotImplementedFileUploadProcessor()

    def pre_check(self, file_path: str) -> bool:
        self._get_subprocessor(file_path)
        return self.subprocessor.pre_check(file_path)

    def process(self, file_path: str, file_upload_registry_hub) -> bool:
        return self.subprocessor.process(file_path, file_upload_registry_hub)

    def _get_subprocessor(self, file_path: str):
        index_tag = open(file_path, encoding="utf-8-sig").readline().strip()
        if index_tag.startswith("Depotuebersicht"):
            self.subprocessor = OnvistaFileUploadDepotProcessor()
        else:
            self.subprocessor = NotImplementedFileUploadProcessor()
            self.message = "File cannot be processed"


class OnvistaFileUploadDepotProcessor:
    message = "Not implemented"
    input_data_df = pd.DataFrame()

    def pre_check(self, file_path: str) -> bool:
        return True

    def process(self, file_path: str, file_upload_registry_hub) -> bool:
        self._get_input_data_df(file_path)
        account_hub = self.get_account_hub(file_upload_registry_hub)
        self._create_assets()
        return True

    def _get_input_data_df(self, file_path: str):
        self.input_data_df = pd.read_csv(file_path, sep=";", skiprows=5, decimal=",")
        self.input_data_df = self.input_data_df.dropna(subset=["Datum"])

    def _create_assets(self):
        for _, row in self.input_data_df.iterrows():
            AssetRepository().std_create_object(
                {
                    "account": account_hub,
                    "date": row["Datum"],
                    "isin": row["ISIN"],
                    "name": row["Bezeichnung"],
                    "amount": row["Stück"],
                    "price": row["Kurs"],
                }
            )
        self.message = f"Created {self.input_data_df.shape[0]} assets"
        return True

    def get_account_hub(self, file_upload_registry_hub):
        return file_upload_registry_hub.account

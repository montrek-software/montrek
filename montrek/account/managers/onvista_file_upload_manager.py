from django.db.models import QuerySet
import pandas as pd
from account.managers.not_implemented_processor import NotImplementedFileUploadProcessor
from asset.repositories.asset_repository import AssetRepository


class OnvistaFileUploadProcessor:
    message = "Not implemented"

    def __init__(self, account_hub: QuerySet):
        self.account_hub = account_hub
        self.subprocessor = NotImplementedFileUploadProcessor()

    def pre_check(self, file_path: str) -> bool:
        self._get_subprocessor(file_path)
        return self.subprocessor.pre_check(file_path)

    def process(self, file_path: str) -> bool:
        return self.subprocessor.process(file_path)

    def post_check(self, file_path: str) -> bool:
        return True

    def _get_subprocessor(self, file_path: str):
        index_tag = open(file_path, encoding="utf-8-sig").readline().strip()
        if index_tag.startswith("Depotuebersicht"):
            self.subprocessor = OnvistaFileUploadDepotProcessor(self.account_hub)
        else:
            self.subprocessor = NotImplementedFileUploadProcessor()
            self.message = "File cannot be processed"


class OnvistaFileUploadDepotProcessor:
    message = "Not implemented"
    input_data_df = pd.DataFrame()

    def __init__(self, account_hub: QuerySet):
        self.account_hub = account_hub

    def pre_check(self, file_path: str) -> bool:
        return True

    def process(self, file_path: str) -> bool:
        self._get_input_data_df(file_path)
        self._create_assets()
        return True

    def _get_input_data_df(self, file_path: str):
        self.input_data_df = pd.read_csv(file_path, sep=";", skiprows=5, decimal=",")
        self.input_data_df = self.input_data_df.dropna(subset=["Datum"])
        self.input_data_df = self.input_data_df.rename(
            columns={
                "Datum": "value_date",
                "Name": "asset_name",
                "Stück": "quantity",
                "Typ": "asset_type",
                "Akt. Geldkurs": "price",
                "ISIN": "asset_isin",
                "WKN": "asset_wkn",
            }
        )
        self.input_data_df["value_date"] = pd.to_datetime(
            self.input_data_df["value_date"], format="%d.%m.%Y"
        )

    def _create_assets(self):
        AssetRepository().create_objects_from_data_frame(
            self.input_data_df,
        )
        self.message = f"Created {self.input_data_df.shape[0]} assets"
        return True

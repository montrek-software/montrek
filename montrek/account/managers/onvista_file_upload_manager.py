from django.db.models import QuerySet
import pandas as pd
from account.managers.not_implemented_processor import NotImplementedFileUploadProcessor
from asset.repositories.asset_repository import AssetRepository
from account.repositories.account_repository import AccountRepository


class OnvistaFileUploadProcessor:
    message = "Not implemented"

    def __init__(self, account_hub: QuerySet):
        self.account_hub = account_hub
        self.subprocessor = NotImplementedFileUploadProcessor()

    def pre_check(self, file_path: str) -> bool:
        self._get_subprocessor(file_path)
        result = self.subprocessor.pre_check(file_path)
        self.message = self.subprocessor.message
        return result

    def process(self, file_path: str) -> bool:
        result = self.subprocessor.process(file_path)
        self.message = self.subprocessor.message
        return result

    def post_check(self, file_path: str) -> bool:
        result = self.subprocessor.post_check(file_path)
        self.message = self.subprocessor.message
        return result

    def _get_subprocessor(self, file_path: str):
        index_tag = open(file_path, encoding="utf-8-sig").readline().strip()
        if index_tag.startswith("Depotuebersicht"):
            self.subprocessor = OnvistaFileUploadDepotProcessor(self.account_hub)
        elif index_tag.startswith("Kontouebersicht"):
            self.subprocessor = OnvistaFileUploadTransactionProcessor(self.account_hub)
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

    def post_check(self, file_path: str) -> bool:
        depot = AccountRepository().get_depot_data(self.account_hub.pk)
        self.input_data_df["account_shares"] = self.input_data_df.apply(
            lambda x: self._get_depot_quantity(x, depot), axis=1
        )
        mismatch_df = self.input_data_df.loc[
            abs(self.input_data_df["account_shares"] - self.input_data_df["quantity"])
            >= 0.0001,
            ["asset_name", "account_shares", "quantity"],
        ]
        if mismatch_df.empty:
            return True
        mismatch_html = mismatch_df.to_html(index=False)
        self.message = f"Mismatch between input data and depot data:\n{mismatch_html}"
        return False

    def _get_input_data_df(self, file_path: str):
        self.input_data_df = pd.read_csv(
            file_path,
            sep=";",
            skiprows=5,
            decimal=",",
            thousands=".",
            parse_dates=["Datum"],
            dayfirst=True,
        )
        self.input_data_df = self.input_data_df.dropna(subset=["Datum"])
        self.input_data_df = self.input_data_df.rename(
            columns={
                "Datum": "value_date",
                "Name": "asset_name",
                "Bestand": "quantity",
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

    def _get_depot_quantity(self, x: pd.Series, depot: QuerySet) -> float:
        asset = depot.filter(asset_name=x.asset_name)
        if len(asset) == 0:
            return 0
        return float(asset.first().total_nominal)


class OnvistaFileUploadTransactionProcessor:
    message = "Not implemented"
    input_data_dfs: dict[str, pd.DataFrame] = {}

    def __init__(self, account_hub: QuerySet):
        self.account_hub = account_hub

    def pre_check(self, file_path: str) -> bool:
        input_df = pd.read_csv(
            file_path,
            sep=";",
            skiprows=5,
            decimal=",",
            thousands=".",
            parse_dates=["Valuta"],
            dayfirst=True,
        )
        input_df["transaction_value"] = input_df["Betrag"].apply(
            lambda x: float(x.replace(".", "").replace(",", ".").replace("EUR", ""))
        )
        self.input_data_dfs["asset_purchase"] = input_df[
            input_df["Verwendungszweck"].str.startswith("Wertpapierkauf")
        ]

        return True

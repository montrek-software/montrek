from typing import Any, Dict
from django.db.models import QuerySet
import pandas as pd
from account.managers.not_implemented_processor import NotImplementedFileUploadProcessor
from mt_accounting.asset.repositories.asset_repository import AssetRepository
from account.repositories.account_repository import AccountRepository
from mt_accounting.transaction.managers.transaction_account_manager import (
    TransactionAccountManager,
)


class OnvistaFileUploadProcessor:
    message = "Not implemented"

    def __init__(self, account_hub: QuerySet, session_data: Dict[str, Any]):
        self.account_hub = account_hub
        self.subprocessor = NotImplementedFileUploadProcessor()
        self.session_data = session_data

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
            self.subprocessor = OnvistaFileUploadDepotProcessor(
                self.account_hub, self.session_data
            )
        elif index_tag.startswith("Kontouebersicht"):
            self.subprocessor = OnvistaFileUploadTransactionProcessor(
                self.account_hub, self.session_data
            )
        else:
            self.subprocessor = NotImplementedFileUploadProcessor()
            self.message = "File cannot be processed"


class OnvistaFileUploadDepotProcessor:
    message = "Not implemented"
    input_data_df = pd.DataFrame()

    def __init__(self, account_hub: QuerySet, session_data: Dict[str, Any]):
        self.account_hub = account_hub
        self.session_data = session_data

    def pre_check(self, file_path: str) -> bool:
        return True

    def process(self, file_path: str) -> bool:
        self._get_input_data_df(file_path)
        self._create_assets()
        return True

    def post_check(self, file_path: str) -> bool:
        depot = AccountRepository(self.session_data).get_depot_data(self.account_hub.pk)
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
        AssetRepository(self.session_data).create_objects_from_data_frame(
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
    input_data_dfs: Dict[str, pd.DataFrame] = {}

    def __init__(self, account_hub: QuerySet, session_data: Dict[str, Any]):
        self.account_hub = account_hub
        self.session_data = session_data

    def pre_check(self, file_path: str) -> bool:
        input_df = pd.read_csv(
            file_path,
            sep=";",
            skiprows=5,
            decimal=",",
            thousands=".",
            parse_dates=["Valuta"],
            dayfirst=True,
            converters={"Verwendungszweck": str},
        )
        input_df["transaction_value"] = input_df["Betrag"].apply(
            lambda x: float(x.replace(".", "").replace(",", ".").replace("EUR", ""))
        )
        self.input_data_dfs["asset_purchase"] = input_df[
            input_df["Verwendungszweck"].str.startswith("Wertpapierkauf")
        ]

        return True

    def process(self, file_path: str) -> bool:
        self._create_asset_transactions()
        return True

    def post_check(self, file_path: str) -> bool:
        return True

    def _extract_transaction_details(self):
        input_df = self.input_data_dfs["asset_purchase"].copy()
        input_df["isin"] = input_df["Verwendungszweck"].str.extract(r"ISIN\s(\w+)")
        input_df["transaction_amount"] = input_df["Verwendungszweck"].apply(
            lambda x: float(x.split(" ")[2].replace(".", "").replace(",", "."))
        )
        input_df["transaction_price"] = (
            (-1) * input_df["transaction_value"] / input_df["transaction_amount"]
        )
        input_df["transaction_date"] = input_df["Valuta"]
        input_df["transaction_description"] = input_df["isin"].apply(
            lambda x: f"Purchase {x}"
        )
        input_df["transaction_party"] = input_df["isin"]
        return input_df

    def _aggregate_asset_transactions(self, input_df):
        return (
            input_df.groupby(["transaction_party", "transaction_date"])
            .agg(
                transaction_amount=("transaction_amount", "sum"),
                transaction_price=(
                    "transaction_amount",
                    lambda x: (input_df.loc[x.index, "transaction_price"] * x).sum()
                    / x.sum(),
                ),
                transaction_description=("transaction_description", "first"),
                link_transaction_asset=("link_transaction_asset", "first"),
            )
            .reset_index()
            .assign(transaction_party_iban="")
        )

    def _init_transactions_manager(self, transactions_df):
        return TransactionAccountManager(
            self.account_hub, transactions_df, self.session_data
        )

    def _prepare_counter_transactions(self, input_df):
        counter_df = (
            input_df.groupby(["transaction_date", "transaction_party"])
            .agg(
                transaction_value=("transaction_value", "sum"),
                transaction_description=("transaction_description", "first"),
            )
            .reset_index()
        )
        counter_df["transaction_party"] += " COUNTER BOOKING"
        counter_df["transaction_party_iban"] = ""
        counter_df["transaction_amount"] = 2 * counter_df["transaction_value"]
        counter_df["transaction_price"] = 1
        return counter_df

    def _create_asset_transactions(self):
        input_df = self._extract_transaction_details()
        self._attach_assets(input_df)
        asset_input_df = self._aggregate_asset_transactions(input_df)
        transaction_account_manager = self._init_transactions_manager(asset_input_df)
        transactions = transaction_account_manager.new_transactions_to_account_from_df()
        counter_transaction_df = self._prepare_counter_transactions(input_df)
        counter_transaction_account_manager = self._init_transactions_manager(
            counter_transaction_df
        )
        counter_transaction_account_manager.new_transactions_to_account_from_df()
        self.message = f"Created {len(transactions)} transactions"
        return True

    def _attach_assets(self, input_df: pd.DataFrame) -> pd.DataFrame:
        assets = AssetRepository().std_queryset()
        input_df["link_transaction_asset"] = input_df["isin"].apply(
            self._get_or_create_asset, args=(assets,)
        )
        return input_df

    def _get_or_create_asset(self, isin: str, assets: QuerySet) -> int:
        asset = assets.filter(asset_isin=isin)
        if len(asset) == 0:
            return AssetRepository(session_data=self.session_data).std_create_object(
                {"asset_isin": isin}
            )
        return asset.first()

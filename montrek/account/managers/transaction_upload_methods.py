from django.db.models import QuerySet
import pandas as pd
from typing import Any, List
from transaction.models import TransactionSatellite
from transaction.managers.transaction_account_manager import TransactionAccountManager


def upload_dkb_transactions(
    account_hub: QuerySet, file_path: str, session_data: dict[str, Any]
) -> List[TransactionSatellite]:
    if account_hub.account_upload_method != "dkb":
        raise AttributeError("Account Upload Method is not of type dkb")
    transactions_df = read_dkb_transactions_from_csv(file_path)
    transaction_account_manager = TransactionAccountManager(
        account_hub, transactions_df, session_data
    )
    return transaction_account_manager.new_transactions_to_account_from_df()


def read_dkb_transactions_from_csv(file_path: str) -> pd.DataFrame:
    transactions_df = pd.read_csv(
        file_path,
        sep=";",
        decimal=",",
        thousands=".",
        encoding="iso-8859-1",
        header=4,
        engine="python",
        parse_dates=["Buchungstag", "Wertstellung"],
        dayfirst=True,
    )
    transaction_df = transactions_df.loc[
        :,
        [
            "Buchungstext",
            "Verwendungszweck",
            "Betrag (EUR)",
            "Buchungstag",
            "Auftraggeber / Begünstigter",
            "Kontonummer",
        ],
    ]
    transaction_df = transaction_df.rename(
        columns={
            "Buchungstag": "transaction_date",
            "Verwendungszweck": "transaction_description",
            "Betrag (EUR)": "transaction_price",
            "Auftraggeber / Begünstigter": "transaction_party",
            "Kontonummer": "transaction_party_iban",
        }
    )
    aggregations = {
        "transaction_description": lambda x: " ".join(x),
        "transaction_price": lambda x: x.sum(),
    }
    transaction_df["transaction_description"] = transaction_df[
        "transaction_description"
    ].astype(str)
    transaction_df["transaction_party"] = transaction_df["transaction_party"].fillna(
        "UNKNOWN"
    )
    transaction_df = (
        transaction_df.groupby(
            ["transaction_date", "transaction_party", "transaction_party_iban"]
        )
        .agg(aggregations)
        .reset_index()
    )
    transaction_df["transaction_amount"] = 1
    return transaction_df

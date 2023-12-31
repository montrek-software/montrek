import pandas as pd
from typing import List
from baseclasses import models as baseclass_models
from baseclasses.repositories.db_helper import new_satellites_bunch_from_df_and_from_hub_link
from transaction.models import TransactionSatellite

def new_transactions_to_account_from_df(
    account_hub_object: baseclass_models.MontrekSatelliteABC,
    transaction_df: pd.DataFrame,
) -> List[baseclass_models.MontrekSatelliteABC]:
    expected_columns = [
        "transaction_date",
        "transaction_amount",
        "transaction_price",
        "transaction_description",
        "transaction_party",
        "transaction_party_iban",
    ]
    if not all([column in transaction_df.columns for column in expected_columns]):
        expected_columns_str = ", ".join(expected_columns)
        got_columns_str = ", ".join(transaction_df.columns)
        raise KeyError(
            f"Wrong columns in transaction_df\n\tGot: {got_columns_str}\n\tExpected: {expected_columns_str}"
        )
    transaction_satellites = new_satellites_bunch_from_df_and_from_hub_link(
        satellite_class=TransactionSatellite,
        import_df=transaction_df,
        to_hub=account_hub_object,
        related_field="link_transaction_account",
    )
    return transaction_satellites

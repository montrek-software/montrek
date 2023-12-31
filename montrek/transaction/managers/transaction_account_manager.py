import pandas as pd
from typing import List
from baseclasses import models as baseclass_models
from baseclasses.repositories.db_helper import (
    new_satellites_bunch_from_df_and_from_hub_link,
)
from transaction.models import TransactionSatellite
from transaction.repositories.transaction_repository import TransactionRepository
from transaction.repositories.transaction_category_repository import ( TransactionCategoryMapRepository )
from transaction.managers.transaction_category_manager import ( TransactionCategoryManager )


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
    transaction_repository = TransactionRepository()
    imported_transactions = []
    for i, row in transaction_df.iterrows():
        row['link_transaction_account'] = account_hub_object
        imported_transactions.append(transaction_repository.std_create_object(row.to_dict()))
    transaction_queryset = transaction_repository.std_queryset().filter(
        id__in=[transaction.id for transaction in imported_transactions]
    )
    transaction_category_map = TransactionCategoryMapRepository().std_queryset().filter(
        account_id=account_hub_object.id
    )
    TransactionCategoryManager().assign_transaction_categories_to_transactions(
        transaction_queryset,
        transaction_category_map,
    )
    return transaction_queryset




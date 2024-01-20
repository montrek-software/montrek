import pandas as pd
from typing import List
from datetime import datetime
from baseclasses import models as baseclass_models
from baseclasses.repositories.db_helper import (
    new_satellites_bunch_from_df_and_from_hub_link,
)
from transaction.models import TransactionSatellite
from transaction.repositories.transaction_repository import TransactionRepository
from transaction.repositories.transaction_category_repository import (
    TransactionCategoryMapRepository,
)
from transaction.managers.transaction_category_manager import TransactionCategoryManager


class TransactionAccountManager:
    def __init__(
        self,
        account_hub_object: baseclass_models.MontrekSatelliteABC,
        transaction_df: pd.DataFrame,
    ):
        self.account_hub_object = account_hub_object
        self.transaction_df = transaction_df
        self.transaction_repository = TransactionRepository()

    def new_transactions_to_account_from_df(
        self,
    ) -> List[baseclass_models.MontrekSatelliteABC]:
        self._validate_transaction_df()
        imported_transactions = self._import_transactions_to_account_from_df()
        transaction_queryset = self._assign_transaction_categories_to_transactions(imported_transactions)
        return transaction_queryset

    def _validate_transaction_df(self):
        expected_columns = [
            "transaction_date",
            "transaction_amount",
            "transaction_price",
            "transaction_description",
            "transaction_party",
            "transaction_party_iban",
        ]
        if not all(
            [column in self.transaction_df.columns for column in expected_columns]
        ):
            expected_columns_str = ", ".join(expected_columns)
            got_columns_str = ", ".join(self.transaction_df.columns)
            raise KeyError(
                f"Wrong columns in transaction_df\n\tGot: {got_columns_str}\n\tExpected: {expected_columns_str}"
            )

    def _import_transactions_to_account_from_df(
        self,
    ):
        imported_transactions = []
        for i, row in self.transaction_df.iterrows():
            row["link_transaction_account"] = self.account_hub_object
            imported_transactions.append(
                self.transaction_repository.std_create_object(row.to_dict())
            )
        return imported_transactions

    def _assign_transaction_categories_to_transactions(
        self,
        imported_transactions: List[baseclass_models.MontrekHubABC],
    ):
        transaction_queryset = self.transaction_repository.std_queryset().filter(
            id__in=[transaction.id for transaction in imported_transactions]
        )
        transaction_category_map = (
            TransactionCategoryMapRepository()
            .std_queryset()
            .filter(account_id=self.account_hub_object.id)
        )
        TransactionCategoryManager().assign_transaction_categories_to_transactions(
            transaction_queryset,
            transaction_category_map,
        )
        return transaction_queryset

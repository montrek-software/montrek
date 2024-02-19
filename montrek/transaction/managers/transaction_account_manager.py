import pandas as pd
from typing import Any, List
from datetime import datetime
from baseclasses import models as baseclass_models
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
        session_data: Dict[str, Any],
    ):
        self.account_hub_object = account_hub_object
        self.transaction_df = transaction_df
        self.session_data = session_data
        self.transaction_repository = TransactionRepository(self.session_data)

    def new_transactions_to_account_from_df(
        self,
    ) -> List[TransactionSatellite]:
        self._validate_transaction_df()
        imported_transactions = self._import_transactions_to_account_from_df()
        transaction_queryset = self._assign_transaction_categories_to_transactions(
            imported_transactions
        )
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
        self.transaction_df["link_transaction_account"] = self.account_hub_object

    def _import_transactions_to_account_from_df(
        self,
    ):
        return self.transaction_repository.create_objects_from_data_frame(
            self.transaction_df
        )

    def _assign_transaction_categories_to_transactions(
        self,
        imported_transactions: List[baseclass_models.MontrekHubABC],
    ):
        transaction_queryset = self.transaction_repository.std_queryset().filter(
            id__in=[transaction.pk for transaction in imported_transactions]
        )
        transaction_category_map = (
            TransactionCategoryMapRepository()
            .std_queryset()
            .filter(account_id=self.account_hub_object.pk)
        )
        TransactionCategoryManager(
            session_data=self.session_data
        ).assign_transaction_categories_to_transactions(
            transaction_queryset,
            transaction_category_map,
        )
        return transaction_queryset

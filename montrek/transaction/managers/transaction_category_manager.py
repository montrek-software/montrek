from typing import Any
from django.db.models import QuerySet
from django.utils import timezone
from transaction.repositories.transaction_category_repository import (
    TransactionCategoryRepository,
)
from transaction.repositories.transaction_repository import TransactionRepository
from transaction.models import TransactionSatellite
from transaction.models import LinkTransactionTransactionCategory
from baseclasses.repositories.db_creator import DbCreator
from account.repositories.account_repository import AccountRepository


class TransactionCategoryManager:
    def __init__(self, session_data: Dict[str, Any]):
        self.session_data = session_data
        self.transaction_category_repository = TransactionCategoryRepository(
            self.session_data
        )
        self.transaction_repository = TransactionRepository(self.session_data)
        self.account_std_queryset = AccountRepository().std_queryset()

    def assign_transaction_categories_to_transactions(
        self, transactions_queryset: QuerySet, transaction_category_map_query: QuerySet
    ):
        for category_map in transaction_category_map_query:
            category = category_map.category
            transaction_category = self._get_transaction_category_or_create(category)
            transactions = self._get_transactions_to_category(
                category_map, transactions_queryset
            )
            self._create_transaction_category_links(transactions, transaction_category)
            if category_map.counter_transaction_account_id:
                self._create_counter_transaction(transactions, category_map)

    def _get_transaction_category_or_create(self, category: str):
        transaction_category_or_none = (
            self.transaction_category_repository.std_queryset().filter(
                typename=category,
            )
        )
        if not transaction_category_or_none.exists():
            self.transaction_category_repository.std_create_object(
                {"typename": category},
            )
            return self.transaction_category_repository.std_queryset().get(
                typename=category,
            )
        return transaction_category_or_none.get()

    def _get_transactions_to_category(self, category_map, transactions_queryset):
        if category_map.is_regex:
            transaction_kwargs = {category_map.field + "__regex": category_map.value}
        else:
            transaction_kwargs = {category_map.field: category_map.value}
        return transactions_queryset.filter(
            **transaction_kwargs,
        )

    def _create_transaction_category_links(self, transactions, transaction_category):
        creation_date = timezone.now()
        for transaction in transactions:
            db_creator = DbCreator(None, [])
            link = db_creator.create_new_link(
                LinkTransactionTransactionCategory,
                transaction,
                transaction_category,
                creation_date,
            )
            link.save()

    def _create_counter_transaction(self, transactions, category_map):
        """
        If the transaction category map has a counter transaction account linked to it, create a  transaction with
        the same traits, but inversed amount.
        """
        counter_transaction_account = self.account_std_queryset.get(
            pk=category_map.counter_transaction_account_id
        )
        for transaction in transactions:
            transaction_traits = self.transaction_repository.object_to_dict(transaction)
            transaction_traits["transaction_amount"] = (
                transaction_traits["transaction_amount"] * -1
            )
            transaction_traits["transaction_party"] = category_map.account_name
            if category_map.bank_account_iban:
                transaction_traits[
                    "transaction_party_iban"
                ] = category_map.bank_account_iban
            transaction_traits["link_transaction_account"] = counter_transaction_account
            transaction_traits.pop("hub_entity_id")
            counter_transaction = TransactionRepository(
                self.session_data
            ).std_create_object(transaction_traits)

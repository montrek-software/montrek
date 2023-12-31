from django.db.models import QuerySet
from django.utils import timezone
from transaction.repositories.transaction_category_repository import (
    TransactionCategoryRepository,
)
from transaction.models import TransactionSatellite
from transaction.models import LinkTransactionTransactionCategory
from baseclasses.repositories.db_creator import DbCreator


class TransactionCategoryManager:
    def __init__(self):
        self.transaction_category_repository = TransactionCategoryRepository({})

    def assign_transaction_categories_to_transactions(
        self, transactions_queryset: QuerySet, transaction_category_map_query: QuerySet
    ):
        for category_map in transaction_category_map_query:

            category = category_map.category
            transaction_category = self._get_transaction_category_or_create(category)
            if category_map.is_regex:
                transaction_kwargs = {category_map.field+'__regex': category_map.value}
            else:
                transaction_kwargs = {category_map.field: category_map.value}
            transactions = transactions_queryset.filter(
                **transaction_kwargs,
            )
            creation_date = timezone.now()
            for transaction in transactions:
                db_creator = DbCreator(transaction, [TransactionSatellite])
                link = db_creator.create_new_link(
                    LinkTransactionTransactionCategory,
                    transaction,
                    transaction_category,
                    creation_date,
                )
                link.save()

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

from django.db.models import QuerySet
from transaction.repositories.transaction_category_repository import (
    TransactionCategoryRepository,
)


class TransactionCategoryManager:
    def __init__(self):
        self.transaction_category_repository = TransactionCategoryRepository({})

    def assign_transaction_categories_to_transactions(
        self, transactions_queryset: QuerySet, transaction_category_map_query: QuerySet
    ):
        pass

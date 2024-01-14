from django.test import TestCase
from transaction.repositories.transaction_repository import TransactionRepository
from transaction.tests.factories.transaction_factories import (
    TransactionSatelliteFactory,
    TransactionCategorySatelliteFactory,
)


class TestTransactionRepository(TestCase):
    def setUp(self):
        self.trans_1 = TransactionSatelliteFactory.create()
        self.trans_2 = TransactionSatelliteFactory.create()
        self.trans_cat_1 = TransactionCategorySatelliteFactory.create(typename="Cat1")
        self.trans_cat_2 = TransactionCategorySatelliteFactory.create(typename="Cat2")
        self.trans_1.hub_entity.link_transaction_transaction_category.add(
            self.trans_cat_1.hub_entity
        )
        self.trans_2.hub_entity.link_transaction_transaction_category.add(
            self.trans_cat_2.hub_entity
        )

    def test_transaction_query_with_filter(self):
        for trans_cat in (self.trans_cat_1, self.trans_cat_2):
            repository = TransactionRepository(
                {"filter": {"transaction_category": trans_cat.typename}}
            )
            queryset = repository.std_queryset()
            self.assertEqual(queryset.count(), 1)
            self.assertEqual(queryset.first().transaction_category, trans_cat.typename)

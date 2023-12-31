from django.test import TestCase
from transaction.tests.factories.transaction_factories import TransactionSatelliteFactory
from transaction.tests.factories.transaction_factories import TransactionCategoryMapSatelliteFactory
from transaction.models import TransactionCategoryMapSatellite
from transaction.managers.transaction_category_manager import TransactionCategoryManager
from transaction.repositories.transaction_repository import TransactionRepository


class TestTransactionCategoryManagers(TestCase):
    def setUp(self):
        TransactionSatelliteFactory.create(
            transaction_party='Starbucks',
        )
        TransactionSatelliteFactory.create(
            transaction_party_iban='NL12ABCD34567890',
        )
        TransactionCategoryMapSatelliteFactory.create(
            field='transaction_party',
            value='Starbucks',
            category='Coffee',
        )
        TransactionCategoryMapSatelliteFactory.create(
            field='transaction_party_iban',
            value='NL12ABCD34567890',
            category='Tea',
        )

    def test_assign_transaction_categories_to_transactions(self):
        transactions = TransactionRepository().std_queryset()
        self.assertEqual(len(transactions), 2)
        transaction_category_map_queryset = TransactionCategoryMapSatellite.objects.all()
        tc_manager = TransactionCategoryManager()
        tc_manager.assign_transaction_categories_to_transactions(transactions,
                                                                 transaction_category_map_queryset)
        transaction_categories = tc_manager.transaction_category_repository.std_queryset()
        self.assertEqual(len(transaction_categories), 2)
        transactions = TransactionRepository().std_queryset()
        self.assertEqual(transactions[0].transaction_category, 'Coffee')
        self.assertEqual(transactions[1].transaction_category, 'Tea')


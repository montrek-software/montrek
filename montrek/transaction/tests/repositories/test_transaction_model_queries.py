from django.test import TestCase
from transaction.repositories.transaction_model_queries import get_transaction_type_by_transaction
from transaction.tests.factories.transaction_factories import TransactionSatelliteFactory
from transaction.tests.factories.transaction_factories import TransactionTypeSatelliteFactory
from transaction.tests.factories.transaction_factories import TransactionTransactionTypeLinkFactory

class TestTransactionTypeModelQueries(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.transaction = TransactionSatelliteFactory()
        cls.transaction_type = TransactionTypeSatelliteFactory()
        TransactionTransactionTypeLinkFactory(from_hub=cls.transaction.hub_entity,
                                              to_hub=cls.transaction_type.hub_entity)

    def test_get_transaction_type_by_transaction(self):
        test_transaction_type = get_transaction_type_by_transaction(self.transaction.hub_entity)
        self.assertEqual(test_transaction_type, self.transaction_type)

from django.test import TestCase
from transaction.repositories.transaction_type_queries import (
    get_transaction_type_by_transaction,
)
from transaction.tests.factories.transaction_factories import (
    TransactionTypeSatelliteFactory,
)
from transaction.tests.factories.transaction_factories import (
    TransactionSatelliteFactory,
)

class TestTransactionTypeModelQueries(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.transaction = TransactionSatelliteFactory()
        cls.transaction_type = TransactionTypeSatelliteFactory(typename="INCOME")
        TransactionTypeSatelliteFactory(typename="EXPANSE")
        cls.transaction.hub_entity.link_transaction_transaction_type.add(
            cls.transaction_type.hub_entity
        )

    def test_get_transaction_type_by_transaction(self):
        test_transaction_type = get_transaction_type_by_transaction(self.transaction)
        self.assertEqual(test_transaction_type, self.transaction_type)

    def test_get_transaction_type_with_none_set(self):
        transaction_without_type = TransactionSatelliteFactory(transaction_price=1.0)
        test_transaction_type = get_transaction_type_by_transaction(
            transaction_without_type
        )
        self.assertEqual(test_transaction_type.typename, "INCOME")
        income_transaction_type_hub = (
            transaction_without_type.hub_entity.link_transaction_transaction_type.all().first()
        )
        self.assertEqual(test_transaction_type.hub_entity, income_transaction_type_hub)

        transaction_without_type = TransactionSatelliteFactory(transaction_price=-1.0)
        test_transaction_type = get_transaction_type_by_transaction(
            transaction_without_type
        )
        self.assertEqual(test_transaction_type.typename, "EXPANSE")
        expanse_transaction_type_hub = (
            transaction_without_type.hub_entity.link_transaction_transaction_type.all().first()
        )
        self.assertEqual(test_transaction_type.hub_entity, expanse_transaction_type_hub)

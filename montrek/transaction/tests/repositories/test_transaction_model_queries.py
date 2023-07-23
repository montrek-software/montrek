from django.test import TestCase
from transaction.repositories.transaction_model_queries import get_transaction_type_by_transaction
from transaction.repositories.transaction_model_queries import get_transaction_category_by_transaction
from transaction.tests.factories.transaction_factories import TransactionSatelliteFactory
from transaction.tests.factories.transaction_factories import TransactionTypeSatelliteFactory
from transaction.tests.factories.transaction_factories import TransactionTransactionTypeLinkFactory
from transaction.tests.factories.transaction_factories import TransactionCategorySatelliteFactory
from transaction.tests.factories.transaction_factories import TransactionTransactionCategoryLinkFactory
from transaction.models import TransactionTransactionTypeLink

class TestTransactionTypeModelQueries(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.transaction = TransactionSatelliteFactory()
        cls.transaction_type = TransactionTypeSatelliteFactory()
        TransactionTransactionTypeLinkFactory(from_hub=cls.transaction.hub_entity,
                                              to_hub=cls.transaction_type.hub_entity)

    def test_get_transaction_type_by_transaction(self):
        test_transaction_type = get_transaction_type_by_transaction(self.transaction)
        self.assertEqual(test_transaction_type, self.transaction_type)

    def test_get_transaction_type_with_none_set(self):
        transaction_without_type = TransactionSatelliteFactory(transaction_price=1.0)
        test_transaction_type = get_transaction_type_by_transaction(transaction_without_type)
        self.assertEqual(test_transaction_type.typename, "INCOME")
        income_transaction_type_hub = TransactionTransactionTypeLink.objects.get(
            from_hub=transaction_without_type.hub_entity
        ).to_hub
        self.assertEqual(test_transaction_type.hub_entity, income_transaction_type_hub)

        transaction_without_type = TransactionSatelliteFactory(transaction_price=-1.0)
        test_transaction_type = get_transaction_type_by_transaction(transaction_without_type)
        self.assertEqual(test_transaction_type.typename, "EXPANSE")
        expanse_transaction_type_hub = TransactionTransactionTypeLink.objects.get(
            from_hub=transaction_without_type.hub_entity
        ).to_hub
        self.assertEqual(test_transaction_type.hub_entity, expanse_transaction_type_hub)

class TestTransactionCategoryModelQueries(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.transaction = TransactionSatelliteFactory()
        cls.transaction_category = TransactionCategorySatelliteFactory()
        TransactionTransactionCategoryLinkFactory(from_hub=cls.transaction.hub_entity,
                                                  to_hub=cls.transaction_category.hub_entity)

    def test_get_transaction_category_by_transaction(self):
        test_transaction_category = get_transaction_category_by_transaction(self.transaction)
        self.assertEqual(test_transaction_category, self.transaction_category)

    def test_get_transaction_category_with_none_set(self):
        transaction_without_type = TransactionSatelliteFactory(transaction_price=1.0)
        test_transaction_category = get_transaction_category_by_transaction(transaction_without_type)
        self.assertEqual(test_transaction_category.typename, 'UNKNOWN')

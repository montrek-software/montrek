from django.test import TestCase
from transaction.repositories.transaction_category_queries import (
    get_transaction_category_by_transaction,
)
from transaction.repositories.transaction_category_queries import (
    set_transaction_category_by_map,
)
from transaction.tests.factories.transaction_factories import (
    TransactionSatelliteFactory,
)
from transaction.tests.factories.transaction_factories import (
    TransactionCategorySatelliteFactory,
)
from transaction.tests.factories.transaction_factories import (
    TransactionCategoryMapSatelliteFactory,
)
from account.tests.factories.account_factories import AccountHubFactory
from transaction.models import TransactionCategoryHub




class TestTransactionCategoryModelQueries(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.transaction = TransactionSatelliteFactory()
        cls.transaction_category = TransactionCategorySatelliteFactory()
        cls.transaction.hub_entity.link_transaction_transaction_category.add(
            cls.transaction_category.hub_entity
        )

    def test_get_transaction_category_by_transaction(self):
        test_transaction_category = get_transaction_category_by_transaction(
            self.transaction
        )
        self.assertEqual(test_transaction_category, self.transaction_category)

    def test_get_transaction_category_with_none_set(self):
        transaction_without_type = TransactionSatelliteFactory(transaction_price=1.0)
        test_transaction_category = get_transaction_category_by_transaction(
            transaction_without_type
        )
        self.assertEqual(test_transaction_category.typename, "UNKNOWN")

    def test_get_transaction_category_with_none_set_check_cat_hubs(self):
        cat_hubs = TransactionCategoryHub.objects
        no_of_hubs = len(cat_hubs.all())
        transaction_without_type = TransactionSatelliteFactory(transaction_price=1.0)
        get_transaction_category_by_transaction(
            transaction_without_type
        )
        self.assertEqual(len(cat_hubs.all()), no_of_hubs + 1)
        transaction_without_type = TransactionSatelliteFactory(transaction_price=1.0)
        get_transaction_category_by_transaction(
            transaction_without_type
        )
        self.assertEqual(len(cat_hubs.all()), no_of_hubs + 1)

    def test_set_transaction_category_by_map(self):
        # Setup
        account = AccountHubFactory()
        transaction_cat_map = TransactionCategoryMapSatelliteFactory(
            field="transaction_party", value="Super PartY", category="Amusement"
        )
        TransactionCategoryMapSatelliteFactory(
            field="transaction_party_iban",
            value="DE123456543",
            category="WORK",
            hub_entity=transaction_cat_map.hub_entity,
        )
        account.link_account_transaction_category_map.add(
            transaction_cat_map.hub_entity
        )
        transaction1 = TransactionSatelliteFactory(
            transaction_party="SuperParty",
        )
        account.link_account_transaction.add(transaction1.hub_entity)

        transaction2 = TransactionSatelliteFactory()
        account.link_account_transaction.add(transaction2.hub_entity)

        transaction3 = TransactionSatelliteFactory()
        account.link_account_transaction.add(transaction3.hub_entity)
        set_transaction_category_by_map(transaction1)
        transcat_1 = get_transaction_category_by_transaction(transaction1)
        self.assertEqual(transcat_1.typename, "AMUSEMENT")


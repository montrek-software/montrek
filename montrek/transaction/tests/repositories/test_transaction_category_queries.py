from django.test import TestCase
from transaction.repositories.transaction_category_queries import (
    get_transaction_category_by_transaction,
)
from transaction.repositories.transaction_category_queries import (
    set_transaction_category_by_map,
)
from transaction.repositories.transaction_category_queries import (
    set_transaction_category_by_map_entry,
)
from transaction.repositories.transaction_category_queries import (
    add_transaction_category_map_entry,
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
from transaction.models import TransactionCategoryHub
from transaction.models import TransactionCategorySatellite
from transaction.models import TransactionCategoryMapSatellite
from account.tests.factories.account_factories import AccountHubFactory
from baseclasses.repositories.db_helper import select_satellite




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

    def test_add_transaction_category_map_entry(self):
        account_hub = AccountHubFactory()
        add_transaction_category_map_entry(
            account_hub,
            {'field': 'transaction_party', 'value': 'Super PartY', 'category': 'Amusement'}
        )
        new_transaction_category_map_hub = (
            account_hub.link_account_transaction_category_map.all()[0]
        )
        new_transaction_category_map_sat = (
            TransactionCategoryMapSatellite.objects.filter(
                hub_entity=new_transaction_category_map_hub
            )[0]
        )
        self.assertEqual(new_transaction_category_map_sat.field, 'transaction_party')
        self.assertEqual(new_transaction_category_map_sat.value, 'Super PartY')
        self.assertEqual(new_transaction_category_map_sat.category, 'Amusement')


    def test_transaction_category_workflow(self):
        # Setup
        transaction_cat_map_entry = TransactionCategoryMapSatelliteFactory(
            field="transaction_party", value="SuperParty", category="Amusement"
        )
        account = (
            transaction_cat_map_entry
            .hub_entity
            .link_transaction_category_map_account.all()[0]
        )
        transaction = TransactionSatelliteFactory(
            transaction_party="SuperParty",
            hub_entity__accounts = [account],
        )
        transaction2 = TransactionSatelliteFactory(
            transaction_party="DuperParty",
            hub_entity__accounts = [account],
        )

        # Transaction has no category by now
        transaction_category = transaction.hub_entity.link_transaction_transaction_category
        self.assertEqual(len(transaction_category.all()), 0)

        # Set category by map
        set_transaction_category_by_map_entry(transaction_cat_map_entry)

        # Transaction has category now
        transaction_category_hub = transaction_category.all()[0]
        transaction_category_satellite = select_satellite(transaction_category_hub,
            TransactionCategorySatellite)
        self.assertEqual(transaction_category_satellite.typename, "AMUSEMENT")
        # The proerty is also affected:
        self.assertEqual(transaction.transaction_category.typename, "AMUSEMENT")
        # The second transaction is not affected
        self.assertEqual(transaction2.transaction_category.typename, "UNKNOWN")

    def test_transaction_category_workflow_regex(self):
        # Setup
        transaction_cat_map_entry = TransactionCategoryMapSatelliteFactory(
            field="transaction_party", 
            value="%Party%", 
            category="Amusement",
            is_regex=True,
        )
        account = (
            transaction_cat_map_entry
            .hub_entity
            .link_transaction_category_map_account.all()[0]
        )
        transaction = TransactionSatelliteFactory(
            transaction_party="SuperParty",
            hub_entity__accounts = [account],
        )
        transaction2 = TransactionSatelliteFactory(
            transaction_party="DuperParty",
            hub_entity__accounts = [account],
        )

        # Set the categories
        set_transaction_category_by_map_entry(transaction_cat_map_entry)
        
        # Both transaction have the category AMUSEMENT

        self.assertEqual(transaction.transaction_category.typename, "AMUSEMENT")
        self.assertEqual(transaction2.transaction_category.typename, "AMUSEMENT")

from django.test import TestCase
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from transaction.tests.factories.transaction_factories import (
    TransactionSatelliteFactory,
)
from transaction.tests.factories.transaction_factories import (
    TransactionCategoryMapSatelliteFactory,
)
from transaction.models import TransactionCategoryMapSatellite
from transaction.managers.transaction_category_manager import TransactionCategoryManager
from transaction.repositories.transaction_repository import TransactionRepository
from transaction.repositories.transaction_category_repository import (
    TransactionCategoryMapRepository,
)
from account.tests.factories.account_factories import AccountStaticSatelliteFactory


class TestTransactionCategoryManagers(TestCase):
    def setUp(self):
        self.base_account = AccountStaticSatelliteFactory.create().hub_entity
        self.secondary_account = AccountStaticSatelliteFactory.create().hub_entity
        TransactionSatelliteFactory.create(
            transaction_party="Starbucks",
            hub_entity__account=self.base_account,
        )
        TransactionSatelliteFactory.create(
            transaction_party_iban="NL12ABCD34567890",
            hub_entity__account=self.base_account,
        )
        TransactionCategoryMapSatelliteFactory.create(
            field="transaction_party",
            value="Starbucks",
            category="Coffee",
            hub_entity__accounts=[self.base_account],
        )
        TransactionCategoryMapSatelliteFactory.create(
            field="transaction_party_iban",
            value="NL12ABCD34567890",
            category="Tea",
            hub_entity__accounts=[self.base_account],
            hub_entity__counter_transaction_accounts=[self.secondary_account],
        )

    def test_assign_transaction_categories_to_transactions(self):
        transactions = TransactionRepository().std_queryset()
        self.assertEqual(len(transactions), 2)
        transaction_category_map_queryset = (
            TransactionCategoryMapRepository().std_queryset()
        )
        tc_manager = TransactionCategoryManager(
            session_data={"user_id": MontrekUserFactory().id}
        )
        tc_manager.assign_transaction_categories_to_transactions(
            transactions, transaction_category_map_queryset
        )
        transaction_categories = (
            tc_manager.transaction_category_repository.std_queryset()
        )
        self.assertEqual(len(transaction_categories), 2)
        transactions = TransactionRepository().std_queryset()
        self.assertEqual(len(transactions), 3)
        transactions_queryset = TransactionRepository().get_queryset_with_account()
        base_transactions = transactions_queryset.filter(
            account_id=self.base_account.id
        )
        self.assertEqual(base_transactions[0].transaction_category, "Coffee")
        self.assertEqual(base_transactions[1].transaction_category, "Tea")
        secondary_transactions = transactions_queryset.filter(
            account_id=self.secondary_account.id
        )
        self.assertEqual(secondary_transactions[0].transaction_category, "Tea")
        self.assertEqual(
            secondary_transactions[0].transaction_amount,
            (-1) * base_transactions[1].transaction_amount,
        )

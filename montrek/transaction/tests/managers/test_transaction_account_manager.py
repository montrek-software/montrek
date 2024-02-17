from decimal import Decimal
import pandas as pd

# Tests for model_utils.py
from django.test import TestCase
from django.utils import timezone
from django.db.models import F, Sum


from account.models import AccountHub
from account.tests.factories import account_factories
from baseclasses.utils import montrek_time
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from transaction.tests.factories import transaction_factories
from transaction.managers.transaction_account_manager import (
    TransactionAccountManager,
)
from transaction.repositories.transaction_repository import TransactionRepository


class TestModelUtils(TestCase):
    def setUp(self):
        self.account = account_factories.AccountStaticSatelliteFactory.create()
        transaction_factories.TransactionCategoryMapSatelliteFactory(
            field="transaction_party",
            value="Test Party 1",
            category="Test Category 1",
            hub_entity__accounts=[self.account.hub_entity],
        )
        self.session_data = {"user_id": MontrekUserFactory().id}

    def test_new_transactions_to_account_from_df_wrong_columns(self):
        account_hub = AccountHub.objects.last()
        test_df = pd.DataFrame({"wrong_column": [1, 2, 3]})
        with self.assertRaises(KeyError) as err:
            TransactionAccountManager(
                account_hub_object=account_hub,
                transaction_df=test_df,
                session_data=self.session_data,
            ).new_transactions_to_account_from_df()
        self.assertEqual(
            str(err.exception),
            "'Wrong columns in transaction_df\\n\\tGot: wrong_column\\n\\tExpected: transaction_date, transaction_amount, transaction_price, transaction_description, transaction_party, transaction_party_iban'",
        )

    def test_new_transactions_to_account_from_df(self):
        account_hub = self.account.hub_entity
        test_df = pd.DataFrame(
            {
                "transaction_date": [
                    montrek_time(2022, 1, 1),
                    montrek_time(2022, 1, 2),
                    montrek_time(2022, 1, 3),
                ],
                "transaction_amount": [1, 2, 3],
                "transaction_price": [251.35, 252.35, -253.35],
                "transaction_description": [
                    "Test transaction 1",
                    "Test transaction 2",
                    "Test transaction 3",
                ],
                "transaction_party": ["Test Party 1", "Test Party 2", "Test Party 3"],
                "transaction_party_iban": [
                    "XX123456789012345678901234567891",
                    "XX123456789012345678901234567890",
                    "XX123456789012345678901234567892",
                ],
            }
        )
        TransactionAccountManager(
            account_hub_object=account_hub,
            transaction_df=test_df,
            session_data=self.session_data,
        ).new_transactions_to_account_from_df()
        new_transactions = (
            TransactionRepository()
            .get_queryset_with_account()
            .filter(link_transaction_account=account_hub)
        )
        self.assertEqual(new_transactions[0].transaction_date, montrek_time(2022, 1, 1))
        self.assertEqual(new_transactions[0].transaction_amount, 1)
        self.assertAlmostEqual(new_transactions[0].transaction_price, Decimal(251.35))
        self.assertEqual(
            new_transactions[0].transaction_description, "Test transaction 1"
        )
        self.assertEqual(new_transactions[0].transaction_category, "Test Category 1")
        self.assertEqual(new_transactions[1].transaction_date, montrek_time(2022, 1, 2))
        self.assertEqual(new_transactions[1].transaction_amount, 2)
        self.assertAlmostEqual(new_transactions[1].transaction_price, Decimal(252.35))
        self.assertEqual(
            new_transactions[1].transaction_description, "Test transaction 2"
        )
        self.assertEqual(new_transactions[2].transaction_date, montrek_time(2022, 1, 3))
        self.assertEqual(new_transactions[2].transaction_amount, 3)
        self.assertAlmostEqual(new_transactions[2].transaction_price, Decimal(-253.35))
        self.assertEqual(
            new_transactions[2].transaction_description, "Test transaction 3"
        )

import pandas as pd
import datetime
# Tests for model_utils.py
from django.test import TestCase
from decimal import Decimal

from account.models import AccountHub
from account.tests.factories import account_factories
from transaction.repositories.transaction_account_queries import new_transaction_to_account
from transaction.repositories.transaction_account_queries import get_transactions_by_account_id
from transaction.repositories.transaction_account_queries import new_transactions_to_account_from_df

ACCOUNTS_UNDER_TEST=1

class TestModelUtils(TestCase):
    @classmethod
    def setUpTestData(cls):
        account_factories.AccountStaticSatelliteFactory.create_batch(ACCOUNTS_UNDER_TEST)

    def test_new_transaction(self):
        account_id = AccountHub.objects.last().id
        new_transaction_to_account(account_id = account_id,
                                   transaction_date=datetime.date(2022, 1, 1),
                                   transaction_amount=1,
                                   transaction_price=251.35,
                                   transaction_type='DEPOSIT',
                                   transaction_category='TRANSFER',
                                   transaction_description='Test transaction')
        new_transaction = get_transactions_by_account_id(account_id=account_id).last()
        self.assertEqual(new_transaction.transaction_date.date(), datetime.date(2022, 1, 1))
        self.assertEqual(new_transaction.transaction_amount, 1)
        self.assertAlmostEqual(new_transaction.transaction_price, Decimal(251.35))
        self.assertEqual(new_transaction.transaction_type, 'DEPOSIT')
        self.assertEqual(new_transaction.transaction_category, 'TRANSFER')
        self.assertEqual(new_transaction.transaction_description, 'Test transaction')


    def test_new_transactions_to_account_from_df_wrong_columns(self):
        account_hub = AccountHub.objects.last()
        test_df = pd.DataFrame({'wrong_column': [1, 2, 3]})
        with self.assertRaises(KeyError) as e:
            new_transactions_to_account_from_df(account_hub = account_hub,
                                                transaction_df = test_df)
        self.assertEqual(str(e.exception), "'Wrong columns in transaction_df\\n\\tGot: wrong_column\\n\\tExpected: transaction_date, transaction_amount, transaction_price, transaction_type, transaction_category, transaction_description'")

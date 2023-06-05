import datetime
# Tests for model_utils.py
from django.test import TestCase
from decimal import Decimal

from account.models import AccountHub
from account.tests.factories import account_factories
from transaction.model_utils import new_transaction_to_account
from transaction.model_utils import get_transactions_by_account_id

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



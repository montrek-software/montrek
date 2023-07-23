import pandas as pd
import datetime
# Tests for model_utils.py
from django.test import TestCase
from django.utils import timezone
from django.db.models import F, Sum

from decimal import Decimal

from account.models import AccountHub
from account.tests.factories import account_factories
from link_tables.tests.factories.link_tables_factories import AccountTransactionLinkFactory
from transaction.tests.factories.transaction_factories import TransactionSatelliteFactory
from transaction.models import TransactionTransactionTypeLink
from transaction.models import TransactionTypeSatellite
from transaction.repositories.transaction_account_queries import new_transaction_to_account
from transaction.repositories.transaction_account_queries import new_transactions_to_account_from_df
from transaction.repositories.transaction_account_queries import get_transactions_by_account_id
from transaction.repositories.transaction_account_queries import get_transactions_by_account_hub
from transaction.repositories.transaction_model_queries import get_transaction_type_by_transaction
from baseclasses.repositories.db_helper import get_link_to_hub
from baseclasses.repositories.db_helper import select_satellite

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
                                   transaction_type='INCOME',
                                   transaction_category='TRANSFER',
                                   transaction_description='Test transaction')
        new_transaction = get_transactions_by_account_id(account_id=account_id).last()
        self.assertEqual(new_transaction.transaction_date.date(), datetime.date(2022, 1, 1))
        self.assertEqual(new_transaction.transaction_amount, 1)
        self.assertAlmostEqual(new_transaction.transaction_price, Decimal(251.35))
        self.assertEqual(new_transaction.transaction_description, 'Test transaction')
        transaction_type_sat = get_transaction_type_by_transaction(new_transaction)
        self.assertEqual(transaction_type_sat.typename, 'INCOME')
        #transaction_cat_sat = get_transaction_category_by_transaction(new_transaction)
        #self.assertEqual(transaction_cat_sat.typename, 'TRANSFER')



    def test_new_transactions_to_account_from_df_wrong_columns(self):
        account_hub = AccountHub.objects.last()
        test_df = pd.DataFrame({'wrong_column': [1, 2, 3]})
        with self.assertRaises(KeyError) as e:
            new_transactions_to_account_from_df(account_hub_object = account_hub,
                                                transaction_df = test_df)
        self.assertEqual(str(e.exception), "'Wrong columns in transaction_df\\n\\tGot: wrong_column\\n\\tExpected: transaction_date, transaction_amount, transaction_price, transaction_description, transaction_party, transaction_party_iban'")

    def test_new_transactions_to_account_from_df(self):
        account_hub = account_factories.AccountHubFactory.create()
        test_df = pd.DataFrame({'transaction_date': [datetime.date(2022, 1, 1), datetime.date(2022, 1, 2), datetime.date(2022, 1, 3)],
                                'transaction_amount': [1, 2, 3],
                                'transaction_price': [251.35, 252.35, -253.35],
                                'transaction_description': ['Test transaction 1', 'Test transaction 2', 'Test transaction 3'],
                                'transaction_party': ['Test Party 1', 'Test Party 2', 'Test Party 3'],
                                'transaction_party_iban': ['XX123456789012345678901234567890', 'XX123456789012345678901234567890', 'XX123456789012345678901234567890'],

                                })
        new_transactions_to_account_from_df(account_hub_object = account_hub,
                                            transaction_df = test_df)
        new_transactions = get_transactions_by_account_hub(account_hub_object=account_hub)
        self.assertEqual(new_transactions[0].transaction_date.date(), datetime.date(2022, 1, 1))
        self.assertEqual(new_transactions[0].transaction_amount, 1)
        self.assertAlmostEqual(new_transactions[0].transaction_price, Decimal(251.35))
        transaction_type_sat = get_transaction_type_by_transaction(new_transactions[0])
        self.assertEqual(transaction_type_sat.typename, 'INCOME')
        #self.assertEqual(new_transactions[0].transaction_category, 'TRANSFER')
        self.assertEqual(new_transactions[0].transaction_description, 'Test transaction 1')
        self.assertEqual(new_transactions[1].transaction_date.date(), datetime.date(2022, 1, 2))
        self.assertEqual(new_transactions[1].transaction_amount, 2)
        self.assertAlmostEqual(new_transactions[1].transaction_price, Decimal(252.35))
        transaction_type_sat = get_transaction_type_by_transaction(new_transactions[1])
        self.assertEqual(transaction_type_sat.typename, 'INCOME')
        #self.assertEqual(new_transactions[1].transaction_category, 'TRANSFER')
        self.assertEqual(new_transactions[1].transaction_description, 'Test transaction 2')
        self.assertEqual(new_transactions[2].transaction_date.date(), datetime.date(2022, 1, 3))
        self.assertEqual(new_transactions[2].transaction_amount, 3)
        self.assertAlmostEqual(new_transactions[2].transaction_price, Decimal(-253.35))
        transaction_type_sat = get_transaction_type_by_transaction(new_transactions[2])
        self.assertEqual(transaction_type_sat.typename, 'EXPANSE')
        #self.assertEqual(new_transactions[2].transaction_category, 'TRANSFER')
        self.assertEqual(new_transactions[2].transaction_description, 'Test transaction 3')

    def test_get_transactions_by_account_hub_for_state_date(self):
        account_hub = AccountHub.objects.create()
        transaction_1 = TransactionSatelliteFactory.create(
            transaction_amount=100,
            transaction_price=1.0,
            state_date_start=timezone.datetime(2023,6,1),
            state_date_end=timezone.datetime(2023,7,1),
        )
        transaction_2 = TransactionSatelliteFactory.create(
            transaction_amount=200,
            transaction_price=1.0,
            state_date_start=timezone.datetime(2023,7,1),
            state_date_end=timezone.datetime.max,
            hub_entity=transaction_1.hub_entity
        )
        transaction_3 = TransactionSatelliteFactory.create(
            transaction_amount=100,
            transaction_price=1.0,
            state_date_start=timezone.datetime(2023,6,15),
            state_date_end=timezone.datetime(2023,7,9),
        )
        transaction_4 = TransactionSatelliteFactory.create(
            transaction_amount=200,
            transaction_price=1.0,
            state_date_start=timezone.datetime(2023,7,9),
            state_date_end=timezone.datetime.max,
            hub_entity=transaction_3.hub_entity
        )
        AccountTransactionLinkFactory.create(
            from_hub=account_hub,
            to_hub=transaction_1.hub_entity)
        AccountTransactionLinkFactory.create(
            from_hub=account_hub,
            to_hub=transaction_3.hub_entity)
        account_transactions = get_transactions_by_account_hub(account_hub)
        self.assertEqual(len(account_transactions), 2)
        account_value = account_transactions.aggregate(total_value=Sum(F('transaction_amount') * F('transaction_price')))['total_value'] or 0. 
        self.assertEqual(account_value, 400)
        account_transactions = get_transactions_by_account_hub(
            account_hub, 
            reference_date=timezone.datetime(2023,7,1))
        self.assertEqual(len(account_transactions), 2)
        account_value = account_transactions.aggregate(total_value=Sum(F('transaction_amount') * F('transaction_price')))['total_value'] or 0.
        self.assertEqual(account_value, 300)
        account_transactions = get_transactions_by_account_hub(
            account_hub,
            reference_date=timezone.datetime(2023,6,1))
        self.assertEqual(len(account_transactions), 1)
        account_value = account_transactions.aggregate(total_value=Sum(F('transaction_amount') * F('transaction_price')))['total_value'] or 0.
        self.assertEqual(account_value, 100)
        account_transactions = get_transactions_by_account_hub(
            account_hub,
            reference_date=timezone.datetime(2023,7,9))
        self.assertEqual(len(account_transactions), 2)
        account_value = account_transactions.aggregate(total_value=Sum(F('transaction_amount') * F('transaction_price')))['total_value'] or 0.
        self.assertEqual(account_value, 400)
        account_transactions = get_transactions_by_account_hub(
            account_hub,
            reference_date=timezone.datetime(2023,5,10))
        self.assertEqual(len(account_transactions), 0)

        



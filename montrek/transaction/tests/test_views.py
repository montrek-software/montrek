from django.test import TestCase

import datetime
from decimal import Decimal

from account.tests.factories import account_factories
from account.models import AccountStaticSatellite
from transaction.model_utils import get_transactions_by_account_id

ACCOUNTS_UNDER_TEST=3
class TestTransactionViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        account_factories.AccountStaticSatelliteFactory.create_batch(ACCOUNTS_UNDER_TEST)

    def test_transaction_add_form(self):
        for acc_no in [acc_sat.hub_entity.id for acc_sat in AccountStaticSatellite.objects.all()]: 
            response = self.client.post(f'/transaction/transaction_add_form/{acc_no}')
            self.assertTemplateUsed(response, 'transaction_add_form.html')

    def test_transaction_add(self):
        for acc_no in [acc_sat.hub_entity.id for acc_sat in AccountStaticSatellite.objects.all()]: 
            self.client.post(f'/transaction/transaction_add/{acc_no}',
                               data={'transaction_amount': 1000, 
                                     'transaction_price': 12.20,
                                     'transaction_description': 'Test Transaction',
                                     'transaction_date':datetime.date(2020, 1, 1)})
            transactions = get_transactions_by_account_id(acc_no) 
            self.assertEqual(len(transactions), 1)
            self.assertEqual(transactions[0].transaction_amount, 1000)
            self.assertEqual(transactions[0].transaction_price,
                             Decimal('12.20'))
            self.assertEqual(transactions[0].transaction_description, 'Test Transaction')
            self.assertEqual(transactions[0].transaction_date,
                             datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc))
            self.assertEqual(transactions[0].transaction_value, Decimal('12200.00'))

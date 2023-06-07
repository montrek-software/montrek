from django.test import TestCase
import datetime
from decimal import Decimal
from account.models import AccountHub
from account.models import AccountStaticSatellite
from account.models import BankAccountPropertySatellite
from account.models import BankAccountStaticSatellite
from account.tests.factories.account_factories import AccountHubFactory
from account.tests.factories.account_factories import AccountStaticSatelliteFactory
from account.tests.factories.account_factories import BankAccountPropertySatelliteFactory
from account.tests.factories.account_factories import BankAccountStaticSatelliteFactory
from transaction.tests.factories.transaction_factories import TransactionHubFactory
from transaction.tests.factories.transaction_factories import TransactionSatelliteFactory
from link_tables.tests.factories.link_tables_factories import AccountTransactionLinkFactory
from baseclasses.model_utils import get_hub_ids_by_satellite_attribute
from transaction.model_utils import get_transactions_by_account_id
from credit_institution.model_utils import get_credit_institution_by_account

# Create your tests here.
class TestAccountViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        AccountStaticSatelliteFactory.create_batch(3)

    def test_new_list_form_returns_correct_html(self):
        response = self.client.get('/account/new_form')
        self.assertTemplateUsed(response, 'new_account_form.html')

    def test_can_create_new_account(self):
        accounts_under_test = len(AccountHub.objects.all())
        self.client.post('/account/new', data={'account_name': 'New Account'})
        self.assertEqual(AccountHub.objects.count(), accounts_under_test + 1)
        self.assertEqual(AccountStaticSatellite.objects.count(),
                         accounts_under_test + 1)
        account_hub = AccountHub.objects.last()
        account_static_satellite = AccountStaticSatellite.objects.last()
        self.assertEqual(account_static_satellite.account_name, 'New Account')
        self.assertEqual(account_static_satellite.hub_entity.id, account_hub.id)
        self.assertEqual(account_static_satellite.account_type, 'Other')

    def test_account_list_returns_correct_html(self):
        response = self.client.post('/account/list')
        self.assertTemplateUsed(response, 'account_list.html')

    def test_account_view_return_correct_html(self):
        for acc_no in [acc_sat.hub_entity.id for acc_sat in AccountStaticSatellite.objects.all()]: 
            response = self.client.post(f'/account/{acc_no}/view')
            self.assertTemplateUsed(response, 'account_view.html')

    def test_account_delete(self):
        accounts_under_test = len(AccountHub.objects.all())
        for acc_no in [acc_sat.hub_entity.id for acc_sat in AccountStaticSatellite.objects.all()]: 
            response = self.client.post(f'/account/{acc_no}/delete')
            accounts_under_test -= 1
            self.assertEqual(AccountHub.objects.count(), 
                             accounts_under_test)
            self.assertEqual(AccountStaticSatellite.objects.count(),
                             accounts_under_test)  

    def test_account_delete_form(self):
        for acc_no in [acc_sat.hub_entity.id for acc_sat in AccountStaticSatellite.objects.all()]: 
            response = self.client.post(f'/account/{acc_no}/delete_form')
            self.assertTemplateUsed(response, 'account_delete_form.html')


class TestBankAccountViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        account_hub = AccountHubFactory()
        account_static_satellite = AccountStaticSatelliteFactory(hub_entity=account_hub)
        transaction_hub = TransactionHubFactory()
        transaction_satellite_1 = TransactionSatelliteFactory(hub_entity=transaction_hub)
        transaction_satellite_2 = TransactionSatelliteFactory(hub_entity=transaction_hub)
        account_transaction_link = AccountTransactionLinkFactory(from_hub=account_hub, to_hub=transaction_hub)
        bank_account_property_satellite = BankAccountPropertySatelliteFactory(hub_entity=account_hub)
        bank_account_static_satellite = BankAccountStaticSatelliteFactory(hub_entity=account_hub)

    def test_bank_account_account_value(self):
        bank_account_satellite = BankAccountPropertySatellite.objects.last()
        self.assertTrue(isinstance(bank_account_satellite.account_value, Decimal))

    def test_bank_account_list_returns_correct_html(self):
        response = self.client.post('/account/list')
        self.assertTemplateUsed(response, 'account_list.html')

    def test_new_bank_account(self):
        accounts_under_test = len(AccountHub.objects.all())
        self.client.post('/account/bank_account/new/New%20Bank%20Account', 
                         data={ 'credit_institution_name': 'Test Bank',
                                'bank_account_iban': 'DE12345678901234567890',
                                })
        self.assertEqual(AccountHub.objects.count(), accounts_under_test + 1)
        self.assertEqual(AccountStaticSatellite.objects.count(),
                         accounts_under_test + 1)
        account_hub = AccountHub.objects.last()
        account_static_satellite = AccountStaticSatellite.objects.last()
        self.assertEqual(account_static_satellite.account_name, 'New Bank Account')
        self.assertEqual(account_static_satellite.hub_entity.id, account_hub.id)
        self.assertEqual(account_static_satellite.account_type, 'BankAccount')
        bank_account_property_satellite = BankAccountPropertySatellite.objects.last()
        self.assertEqual(bank_account_property_satellite.hub_entity.id, account_hub.id)
        bank_account_static_satellite = BankAccountStaticSatellite.objects.last()
        self.assertEqual(bank_account_static_satellite.bank_account_iban,
                         'DE12345678901234567890')
        credit_institution = get_credit_institution_by_account(account_hub).last()
        self.assertEqual(credit_institution.credit_institution_name, 'Test Bank')

    def test_bank_account_returns_correct_html(self):
        for acc_no in [acc_sat.hub_entity.id for acc_sat in
                       BankAccountStaticSatellite.objects.all()]: 
            response = self.client.post(f'/account/{acc_no}/bank_account_view')
            self.assertTemplateUsed(response, 'bank_account_view.html')



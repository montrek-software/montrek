from django.test import TestCase
from account.models import AccountHub
from account.models import AccountStaticSatellite
from account.tests.factories import account_factories

ACCOUNTS_UNDER_TEST=3
# Create your tests here.
class test_new_account(TestCase):
    @classmethod
    def setUpTestData(cls):
        account_factories.AccountStaticSatelliteFactory.create_batch(ACCOUNTS_UNDER_TEST)

    def test_new_list_form_returns_correct_html(self):
        response = self.client.get('/account/new_form')
        self.assertTemplateUsed(response, 'new_account_form.html')

    def test_can_create_new_account(self):
        self.client.post('/account/new', data={'account_name': 'New Account'})
        self.assertEqual(AccountHub.objects.count(), ACCOUNTS_UNDER_TEST + 1)
        self.assertEqual(AccountStaticSatellite.objects.count(),
                         ACCOUNTS_UNDER_TEST + 1)
        account_hub = AccountHub.objects.last()
        account_static_satellite = AccountStaticSatellite.objects.last()
        self.assertEqual(account_static_satellite.account_name, 'New Account')
        self.assertEqual(account_static_satellite.hub_entity.id, account_hub.id)

    def test_account_list_returns_correct_html(self):
        response = self.client.post('/account/list')
        self.assertTemplateUsed(response, 'account_list.html')

    def test_account_view_return_correct_html(self):
        for acc_no in range(1, ACCOUNTS_UNDER_TEST + 1): 
            response = self.client.post(f'/account/{acc_no}/view')
            self.assertTemplateUsed(response, 'account_view.html')

    def test_account_delete(self):
        for acc_no in range(1, ACCOUNTS_UNDER_TEST + 1): 
            response = self.client.post(f'/account/{acc_no}/delete')
            self.assertEqual(AccountHub.objects.count(), ACCOUNTS_UNDER_TEST - acc_no)
            self.assertEqual(AccountStaticSatellite.objects.count(),
                             ACCOUNTS_UNDER_TEST - acc_no)  

    def test_account_delete_form(self):
        for acc_no in range(1, ACCOUNTS_UNDER_TEST + 1): 
            response = self.client.post(f'/account/{acc_no}/delete_form')
            self.assertTemplateUsed(response, 'account_delete_form.html')

from django.test import TestCase
from account.models import AccountHub
from account.models import AccountStaticSatellite
from account.tests.factories import account_factories

# Create your tests here.
class test_new_account(TestCase):
    @classmethod
    def setUpTestData(cls):
        account_factories.AccountStaticSatelliteFactory.create_batch(3)

    def test_new_list_form_returns_correct_html(self):
        response = self.client.get('/account/new_form')
        self.assertTemplateUsed(response, 'new_account_form.html')

    def test_can_create_new_account(self):
        self.client.post('/account/new', data={'account_name': 'New Account'})
        self.assertEqual(AccountHub.objects.count(), 4)
        self.assertEqual(AccountStaticSatellite.objects.count(), 4)
        account_hub = AccountHub.objects.last()
        account_static_satellite = AccountStaticSatellite.objects.last()
        self.assertEqual(account_static_satellite.account_name, 'New Account')
        self.assertEqual(account_static_satellite.hub_entity.id, account_hub.id)



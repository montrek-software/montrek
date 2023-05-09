from django.test import TestCase
from account.models import AccountHub
from account.models import AccountStaticSatellite
from account.tests.factories import account_factories
from baseclasses.model_utils import get_hub_ids_by_satellite_attribute

# Create your tests here.
class TestAccountViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        account_factories.AccountStaticSatelliteFactory.create_batch(3)

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

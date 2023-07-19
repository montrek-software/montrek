from django.test import TestCase
from account.repositories.account_model_queries import new_account
from account.models import AccountStaticSatellite

class TestAccountModelQueries(TestCase):
    def test_new_account(self):
        account = new_account('test')
        account_sat_db = AccountStaticSatellite.objects.last()
        self.assertEqual(account, account_sat_db.hub_entity)
        self.assertEqual(account_sat_db.account_name, 'test')
        self.assertEqual(account_sat_db.account_type, 'Other')






from django.test import TestCase
from account.repositories import account_model_queries as amq
from account.models import AccountStaticSatellite
from account.tests.factories import account_factories


class TestAccountModelQueries(TestCase):
    def test_new_account(self):
        account = amq.new_account("test")
        account_sat_db = AccountStaticSatellite.objects.last()
        self.assertEqual(account, account_sat_db.hub_entity)
        self.assertEqual(account_sat_db.account_name, "test")
        self.assertEqual(account_sat_db.account_type, "Other")


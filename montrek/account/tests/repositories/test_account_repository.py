from django.test import TestCase
from depot.tests.factories.depot_factories import DepotAccountFactory
from account.repositories.account_repository import AccountRepository


class TestDepotAccountRepository(TestCase):
    def setUp(self):
        self.depot_account = DepotAccountFactory.create()

    def test_depot_account_std_query(self):
        accounts = AccountRepository().std_queryset()
        self.assertEqual(accounts.count(), 1)

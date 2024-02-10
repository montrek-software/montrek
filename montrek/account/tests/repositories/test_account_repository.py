from django.test import TestCase
from depot.tests.factories.depot_factories import DepotAccountFactory
from account.repositories.account_repository import AccountRepository


class TestDepotAccountRepository(TestCase):
    def setUp(self):
        self.depot_account = DepotAccountFactory.create()

    def test_depot_account_std_query(self):
        repository = AccountRepository()
        accounts = repository.std_queryset()
        self.assertEqual(accounts.count(), 1)
        account = accounts.first()
        assets = repository.get_depot_data(accounts.first().pk)
        self.assertEqual(assets.count(), 3)

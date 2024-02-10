from decimal import Decimal
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
        self.assertEqual(account.account_cash, 1)
        self.assertAlmostEqual(account.account_value, Decimal(4.6))
        self.assertAlmostEqual(account.account_depot_value, Decimal(3.6))
        self.assertAlmostEqual(account.account_depot_book_value, Decimal(3.0))
        self.assertAlmostEqual(account.account_depot_pnl, Decimal(0.6))
        self.assertAlmostEqual(account.account_depot_performance, Decimal(0.2))

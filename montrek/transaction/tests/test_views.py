from django.test import TestCase
from transaction.tests.factories.transaction_factories import TransactionSatelliteFactory
from account.tests.factories.account_factories import AccountHubFactory


class TestTransactionView(TestCase):
    @classmethod
    def setUpTestData(cls):
        account_hub = AccountHubFactory.create()
        cls.test_transaction = TransactionSatelliteFactory.create()
        account_hub.link_account_transaction.add(cls.test_transaction.hub_entity)

    def test_transaction_view(self):
        response = self.client.get(f'/transaction/{self.test_transaction.id}/view/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transaction_view.html')

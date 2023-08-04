from django.test import TestCase
from transaction.tests.factories.transaction_factories import TransactionSatelliteFactory


class TestTransactionView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_transaction = TransactionSatelliteFactory.create()

    def test_transaction_view(self):
        response = self.client.get(f'/transaction/{self.test_transaction.id}/view/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transaction_view.html')

    def test_transaction_view_post(self):
        response = self.client.post(f'/transaction/{self.test_transaction.id}/view/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transaction_view.html')


from django.test import TestCase
from transaction.tests.factories.transaction_factories import (
    TransactionSatelliteFactory,
)


class TestTransactionView(TestCase):
    def setUp(self):
        self.test_transaction = TransactionSatelliteFactory.create()

    def test_transaction_view(self):
        response = self.client.get(f"/transaction/{self.test_transaction.hub_entity.id}/details/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_details.html")

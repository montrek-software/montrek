from django.test import TestCase
from django.urls import reverse
from transaction.tests.factories.transaction_factories import (
    TransactionSatelliteFactory,
)
from account.tests.factories.account_factories import AccountStaticSatelliteFactory


class TestTransactionView(TestCase):
    def setUp(self):
        self.test_transaction = TransactionSatelliteFactory.create()

    def test_transaction_view(self):
        response = self.client.get(f"/transaction/{self.test_transaction.hub_entity.id}/details/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_details.html")

class TestTransactionCreateFromAccount(TestCase):
    def setUp(self):
        self.account = AccountStaticSatelliteFactory().hub_entity 

    def test_view_return_correct_html(self):
        url = reverse("transaction_create_from_account", kwargs={"account_id": self.account.id})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_create.html")

    def test_view_post_success(self):
        url = reverse("transaction_create_from_account", kwargs={"account_id": self.account.id})
        data = {
            "transaction_date": "2023-12-25",
            "transaction_amount": 100,
            "transaction_price": 1.,
            "transaction_description": "test transaction",
            "transaction_party": "test counterparty",
            "transaction_party_iban": "XX12345678901234567890",
            "link_transaction_account": self.account.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.account.link_account_transaction.count(), 1)

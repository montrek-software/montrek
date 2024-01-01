from django.test import TestCase
from django.urls import reverse
from transaction.tests.factories.transaction_factories import (
    TransactionSatelliteFactory,
    TransactionCategoryMapSatelliteFactory,
    TransactionCategorySatelliteFactory,
)
from transaction.repositories.transaction_repository import TransactionRepository
from account.tests.factories.account_factories import AccountStaticSatelliteFactory


class TestTransactionView(TestCase):
    def setUp(self):
        self.test_transaction = TransactionSatelliteFactory.create()

    def test_transaction_view(self):
        response = self.client.get(
            f"/transaction/{self.test_transaction.hub_entity.id}/details/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_details.html")


class TestTransactionCreateFromAccount(TestCase):
    def setUp(self):
        self.account = AccountStaticSatelliteFactory().hub_entity

    def test_view_return_correct_html(self):
        url = reverse(
            "transaction_create_from_account", kwargs={"account_id": self.account.id}
        )
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_create.html")

    def test_view_post_success(self):
        url = reverse(
            "transaction_create_from_account", kwargs={"account_id": self.account.id}
        )
        data = {
            "transaction_date": "2023-12-25",
            "transaction_amount": 100,
            "transaction_price": 1.0,
            "transaction_description": "test transaction",
            "transaction_party": "test counterparty",
            "transaction_party_iban": "XX12345678901234567890",
            "link_transaction_account": self.account.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.account.link_account_transaction.count(), 1)


class TestTransactionUpdateView(TestCase):
    def setUp(self):
        self.test_transaction = TransactionSatelliteFactory.create()
        self.test_transaction_category = TransactionCategorySatelliteFactory.create(
            typename="TestCat"
        )

    def test_view_return_correct_html(self):
        url = reverse(
            "transaction_update",
            kwargs={"pk": self.test_transaction.hub_entity.id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_create.html")

    def test_view_post_success(self):
        url = reverse(
            "transaction_update",
            kwargs={"pk": self.test_transaction.hub_entity.id},
        )
        transaction_repository = TransactionRepository()
        transaction = transaction_repository.std_queryset().first()
        data = transaction_repository.object_to_dict(transaction)
        data.update(
            {
                "link_transaction_transaction_category": self.test_transaction_category.hub_entity.id
            }
        )
        data.pop("link_transaction_transaction_type")
        data.pop("link_transaction_asset")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(transaction.transaction_category, "TestCat")


class TestTransactionCategoryMapDetailsView(TestCase):
    def setUp(self):
        self.test_transaction_category_map = TransactionCategoryMapSatelliteFactory()
        self.account = (
            self.test_transaction_category_map.hub_entity.link_transaction_category_map_account.first()
        )

    def test_view_return_correct_html(self):
        url = reverse(
            "transaction_category_map_details",
            kwargs={
                "pk": self.test_transaction_category_map.hub_entity.id,
                "account_id": self.account.id,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_details.html")


class TestTransactionCategoryMapCreateView(TestCase):
    def setUp(self):
        self.account = AccountStaticSatelliteFactory().hub_entity
        self.test_transaction = TransactionSatelliteFactory(
            transaction_party="123",
            hub_entity__account=self.account,
        )

    def test_view_return_correct_html(self):
        url = reverse(
            "transaction_category_map_create",
            kwargs={"account_id": self.account.id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_create.html")

    def test_view_post_success(self):
        url = reverse(
            "transaction_category_map_create",
            kwargs={"account_id": self.account.id},
        )
        data = {
            "field": "transaction_party",
            "value": "123",
            "category": "TestCat",
            "is_regex": False,
            "link_transaction_category_map_account": self.account.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.account.link_account_transaction_category_map.count(), 1)
        self.assertEqual(
            self.test_transaction.hub_entity.link_transaction_transaction_category.count(),
            1,
        )

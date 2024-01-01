from django.test import TestCase
from django.urls import reverse
from currency.repositories.currency_repository import CurrencyRepository
from currency.tests.factories.currency_factories import CurrencyStaticSatelliteFactory

class TestCurrencyCreate(TestCase):
    def test_currency_create_returns_correct_html(self):
        url = reverse("currency_create")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_create.html")

    def test_view_post_success(self):
        url = reverse("currency_create")
        response = self.client.post(
            url,
            {
                "ccy_name": "test_currency",
                "ccy_code": "USD",
            },
        )
        self.assertEqual(response.status_code, 302)
        currency = CurrencyRepository().std_queryset().first()
        self.assertEqual(currency.ccy_name, "test_currency")
        self.assertEqual(currency.ccy_code, "USD")

class TestCurrencyDetails(TestCase):
    def test_currency_details_returns_correct_html(self):
        ccy = CurrencyStaticSatelliteFactory()
        url = reverse("currency_details", kwargs={"pk": ccy.id})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_details.html")

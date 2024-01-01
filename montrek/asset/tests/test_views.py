from django.test import TestCase
from django.urls import reverse

from asset import views as asset_views
from asset.repositories.asset_repository import AssetRepository
from currency.tests.factories.currency_factories import CurrencyStaticSatelliteFactory


class TestAssetOverview(TestCase):
    def test_asset_overview_returns_correct_html(self):
        url = reverse("asset")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_table.html")


class TestAssetCreateView(TestCase):
    def test_asset_create_returns_correct_html(self):
        url = reverse("asset_create")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_create.html")

    def test_view_post_success(self):
        ccy_code = CurrencyStaticSatelliteFactory(ccy_code="USD")
        url = reverse("asset_create")
        response = self.client.post(
            url,
            {
                "asset_name": "test_asset",
                "asset_type": "ETF",
                "asset_isin": "US1234567890",
                "asset_wkn": "123456",
                "link_asset_currency": ccy_code.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        asset = AssetRepository().std_queryset().first()
        self.assertEqual(asset.asset_name, "test_asset")
        self.assertEqual(asset.asset_type, "ETF")
        self.assertEqual(asset.asset_isin, "US1234567890")
        self.assertEqual(asset.asset_wkn, "123456")
        self.assertEqual(asset.ccy_code, "USD")

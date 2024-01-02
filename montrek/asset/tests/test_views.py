from django.test import TestCase
from django.urls import reverse

from asset.repositories.asset_repository import AssetRepository
from asset.tests.factories.asset_factories import AssetStaticSatelliteFactory
from asset.models import AssetHub
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

class TestAssetDetailsView(TestCase):
    def test_asset_details_returns_correct_html(self):
        asset = AssetStaticSatelliteFactory()
        url = reverse("asset_details", kwargs={"pk": asset.hub_entity.id})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_details.html")

class TestAssetUpdateView(TestCase):
    def test_asset_update_returns_correct_html(self):
        asset = AssetStaticSatelliteFactory()
        url = reverse("asset_update", kwargs={"pk": asset.hub_entity.id})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_create.html")

    def test_update_currency(self):
        ccy_usd = CurrencyStaticSatelliteFactory(ccy_code="USD")
        ccy_eur = CurrencyStaticSatelliteFactory(ccy_code="EUR")
        asset = AssetStaticSatelliteFactory.create()
        asset.hub_entity.link_asset_currency.add(ccy_eur.hub_entity)
        asset_repository = AssetRepository()
        asset = asset_repository.std_queryset().first()
        url = reverse("asset_update", kwargs={"pk": asset.id})
        data = asset_repository.object_to_dict(asset)
        data["link_asset_currency"] = ccy_usd.hub_entity.id
        data["asset_isin"] = "A"
        data["asset_wkn"] = "B"
        data["price"] = 1
        data["value_date"] = "2020-01-01"
        data["asset_type"] = "ETF"
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        assets = AssetRepository().std_queryset()
        self.assertEqual(assets.count(), 1)
        self.assertEqual(assets.first().ccy_code, "USD")

from django.test import TestCase
from asset.repositories.asset_repository import AssetRepository
from asset.tests.factories.asset_factories import (
    AssetHubFactory,
    AssetTimeSeriesSatelliteFactory,
)


class TestAssetPricesQuery(TestCase):
    def setUp(self):
        self.asset_hub = AssetHubFactory.create()
        self.asset_price_3 = AssetTimeSeriesSatelliteFactory.create(
            hub_entity=self.asset_hub, price=102, value_date="2024-02-03"
        )
        self.asset_price_1 = AssetTimeSeriesSatelliteFactory.create(
            hub_entity=self.asset_hub, price=100, value_date="2024-02-01"
        )
        self.asset_price_4 = AssetTimeSeriesSatelliteFactory.create(
            hub_entity=self.asset_hub, price=103, value_date="2024-02-04"
        )
        self.asset_price_2 = AssetTimeSeriesSatelliteFactory.create(
            hub_entity=self.asset_hub, price=101, value_date="2024-02-02"
        )

    def test_get_asset_prices(self):
        asset_repository = AssetRepository()
        asset_prices = asset_repository.get_asset_prices(asset_id=self.asset_hub.pk)
        self.assertEqual(len(asset_prices), 3)
        self.assertEqual(asset_prices[0].asset_id, 1)
        self.assertEqual(asset_prices[0].price, 100)
        self.assertEqual(asset_prices[1].asset_id, 2)
        self.assertEqual(asset_prices[1].price, 200)
        self.assertEqual(asset_prices[2].asset_id, 3)
        self.assertEqual(asset_prices[2].price, 300)

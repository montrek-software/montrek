from django.test import TestCase
from asset.repositories.asset_repository import AssetRepository
from asset.tests.factories.asset_factories import (
    AssetHubFactory,
    AssetTimeSeriesSatelliteFactory,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory


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
        self.user = MontrekUserFactory()
        self.asset_repository = AssetRepository(session_data={"user_id": self.user.id})

    def test_get_asset_prices(self):
        asset_prices = self.asset_repository.get_asset_prices(
            asset_id=self.asset_hub.pk
        )
        self.assertEqual(len(asset_prices), 4)
        self.assertEqual(asset_prices[0].price, 100)
        self.assertEqual(asset_prices[1].price, 101)
        self.assertEqual(asset_prices[2].price, 102)
        self.assertEqual(asset_prices[3].price, 103)

    def test_update_asset_price(self):
        self.asset_repository.std_create_object(
            {
                "price": 104,
                "value_date": "2024-02-02",
                "hub_entity_id": self.asset_hub.id,
            }
        )
        asset_prices = self.asset_repository.get_asset_prices(
            asset_id=self.asset_hub.pk
        )
        self.assertEqual(len(asset_prices), 4)
        self.assertEqual(asset_prices[1].price, 104)

    def test_filter_for_session_data(self):
        self.asset_repository.session_data.update(
            {"start_date": "2024-02-02", "end_date": "2024-02-03"}
        )
        asset_prices = self.asset_repository.get_asset_prices(
            asset_id=self.asset_hub.pk
        )
        self.assertEqual(len(asset_prices), 2)
        self.assertEqual(asset_prices[0].price, 101)
        self.assertEqual(asset_prices[1].price, 102)

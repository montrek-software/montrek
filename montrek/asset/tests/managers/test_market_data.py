from django.test import TestCase
from asset.tests.factories.asset_factories import (
    AssetStaticSatelliteFactory,
    AssetLiquidSatelliteFactory,
)
from asset.models import AssetHub
from asset.managers.market_data import update_asset_prices
from asset.managers.market_data import get_isin_asset_map

class TestMarketData(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.asset_1 = AssetStaticSatelliteFactory(
            asset_name='Test ETF 1',
            asset_type='ETF',
        )
        AssetLiquidSatelliteFactory(
            hub_entity=cls.asset_1.hub_entity,
            asset_isin='IE00BYZK4669',
            asset_wkn='A2ANH1',
        )
        cls.asset_2 = AssetStaticSatelliteFactory(
            asset_name='Test Stock 1',
            asset_type='STOCK',
        )
        AssetLiquidSatelliteFactory(
            hub_entity=cls.asset_2.hub_entity,
            asset_isin='US0378331005',
            asset_wkn='865985',
        )
        AssetStaticSatelliteFactory(
            asset_name='Test REAL_ESTATE',
            asset_type='REAL_ESTATE',
        )

    def test_get_isin_asset_map(self):
        test_dict = get_isin_asset_map()
        self.assertDictEqual(test_dict,
                             {'IE00BYZK4669': self.asset_1.hub_entity.id,
                              'US0378331005': self.asset_2.hub_entity.id})

    def test_get_market_data(self):
        isin_asset_map = get_isin_asset_map()
        update_asset_prices(isin_asset_map)
        for asset in AssetHub.objects.all():
            asset_static = asset.asset_static_satellite.last()
            asset_ts = asset.asset_time_series_satellite.all()
            if not asset_static.is_liquid:
                self.assertEqual(asset_ts.count(), 0)
                continue
            self.assertEqual(asset_ts.count(), 1)
            asset_ts = asset_ts.first()
            self.assertEqual(asset_ts.price, 100)



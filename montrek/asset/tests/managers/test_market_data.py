from django.test import TestCase
from asset.tests.factories.asset_factories import (
    AssetStaticSatelliteFactory,
    AssetLiquidSatelliteFactory,
    AssetTimeSeriesSatelliteFactory,
)

class TestMarketData(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass
    def test_get_market_data(self):

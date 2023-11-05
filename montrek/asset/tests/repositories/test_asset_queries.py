from django.test import TestCase
from asset.tests.factories import asset_factories
from asset.repositories import asset_queries
from asset.models import AssetLiquidSatellite

class TestAssetQueries(TestCase):
    def setUp(self):
        self.isin = "US0378331005"
        self.asset = asset_factories.AssetLiquidSatelliteFactory(
            asset_isin=self.isin
        )

    def test_find_asset_hub_by_isin_or_create(self):
        # Find existing Asset
        found_asset, created = asset_queries.find_asset_hub_by_isin_or_create(isin=self.isin)
        self.assertEqual(created, False)
        self.assertEqual(found_asset, self.asset.hub_entity)
        # Create and return new Asset
        new_asset, created = asset_queries.find_asset_hub_by_isin_or_create(isin="US0378331006")
        self.assertEqual(created, True)
        new_asset_sat = AssetLiquidSatellite.objects.get(hub_entity=new_asset)
        self.assertEqual(new_asset_sat.asset_isin, "US0378331006")

from django.test import TestCase
from asset.tests.factories import asset_factories
from asset.repositories import asset_queries
from asset.models import AssetStaticSatellite

class TestAssetQueries(TestCase):
    def setUp(self):
        self.isin = "US0378331005"
        self.asset = asset_factories.AssetStaticSatelliteFactory(
            isin=self.isin
        )

    def test_find_asset_hub_by_isin_or_create(self):
        # Find existing Asset
        found_asset = asset_queries.find_asset_hub_by_isin_or_create(isin=self.isin) 
        self.assertEqual(found_asset, self.asset.hub_entity)
        # Create and return new Asset
        new_asset = asset_queries.find_asset_hub_by_isin_or_create(isin="US0378331006")
        new_asset_sat = AssetStaticSatellite.objects.get(hub_entity=new_asset)
        self.assertEqual(new_asset_sat.isin, "US0378331006")

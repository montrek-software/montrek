from django.test import TestCase

from transaction.repositories import transaction_model_queries
from transaction.tests.factories import transaction_factories
from asset.tests.factories import asset_factories

class TestTransactionModelQueries(TestCase):
    def test_add_asset_to_transaction(self):
        asset_hub = asset_factories.AssetHubFactory()
        asset_static = asset_factories.AssetStaticSatelliteFactory(
            hub_entity = asset_hub,
            asset_name = 'TestName',
        )
        asset_liquid = asset_factories.AssetLiquidSatelliteFactory(
            hub_entity = asset_hub,
            asset_isin = 'US0378331005',
        )
        transaction = transaction_factories.TransactionSatelliteFactory()
        transaction_model_queries.add_asset_to_transaction(
            asset_hub=asset_static.hub_entity,
            transaction_hub=transaction.hub_entity,
        )
        transaction_asset = transaction_model_queries.get_transaction_asset_hub(
            transaction_hub=transaction.hub_entity,
        )
        self.assertEqual(transaction_asset, asset_hub)
        transaction_asset_static = transaction_model_queries.get_transaction_asset_static_satellite(
            transaction_hub=transaction.hub_entity,
        )
        self.assertEqual(transaction_asset_static, asset_static)
        self.assertEqual(transaction_asset_static.asset_name, 'TestName')
        transaction_asset_liquid = transaction_model_queries.get_transaction_asset_liquid_satellite(
            transaction_hub=transaction.hub_entity,
        )
        self.assertEqual(transaction_asset_liquid, asset_liquid)
        self.assertEqual(transaction_asset_liquid.asset_isin, 'US0378331005')

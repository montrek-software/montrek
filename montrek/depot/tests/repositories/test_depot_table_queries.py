import datetime
from django.test import TestCase 

from depot.repositories.depot_table_queries import get_depot_asset_table
from account.tests.factories import account_factories
from asset.tests.factories import asset_factories
from transaction.tests.factories import transaction_factories

class TestDepotTable(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.account = account_factories.AccountHubFactory.create()
        asset_1 = asset_factories.AssetStaticSatelliteFactory(
            asset_name='Test Asset 1',
            asset_type='ETF',
        )
        asset_factories.AssetLiquidSatelliteFactory(
            hub_entity = asset_1.hub_entity,
            asset_isin = 'DE1234567891',
            asset_wkn = 'TEST12',
        )
        asset_2 = asset_factories.AssetStaticSatelliteFactory(
            asset_name='Test Asset 2',
            asset_type='ETF',
        )
        asset_factories.AssetLiquidSatelliteFactory(
            hub_entity = asset_2.hub_entity,
            asset_isin = 'DE4564567891',
            asset_wkn = 'TEST45',
        )
        trans1_1 = transaction_factories.TransactionSatelliteFactory(
            transaction_price = 100,
            transaction_amount = 10,
            transaction_date = datetime.date(2023,10,10), 
        )
        cls.account.link_account_transaction.add(trans1_1.hub_entity)
        trans1_1.hub_entity.link_transaction_asset.add(asset_1.hub_entity)
        trans1_2 = transaction_factories.TransactionSatelliteFactory(
            transaction_price = 150,
            transaction_amount = 20,
            transaction_date = datetime.date(2023,10,1), 
        )
        cls.account.link_account_transaction.add(trans1_2.hub_entity)
        trans1_2.hub_entity.link_transaction_asset.add(asset_1.hub_entity)
        trans2_1 = transaction_factories.TransactionSatelliteFactory(
            transaction_price = 90,
            transaction_amount = 50,
            transaction_date = datetime.date(2023,10,5), 
        )
        cls.account.link_account_transaction.add(trans2_1.hub_entity)
        trans2_1.hub_entity.link_transaction_asset.add(asset_2.hub_entity)

    def test_get_depot_asset_table(self):
        depot_asset_table_data = get_depot_asset_table(self.account.id)
        self.assertEqual(len(depot_asset_table_data), 2)
        self.assertEqual(depot_asset_table_data[0].asset_name, 'Test Asset 1')
        self.assertEqual(depot_asset_table_data[0].asset_isin, 'DE1234567891')
        self.assertEqual(depot_asset_table_data[0].asset_wkn, 'TEST12')
        self.assertEqual(depot_asset_table_data[0].total_nominal, 30)
        self.assertEqual(depot_asset_table_data[0].book_value, 100*10+150*20)
        self.assertEqual(depot_asset_table_data[1].asset_name, 'Test Asset 2')
        self.assertEqual(depot_asset_table_data[1].asset_isin, 'DE4564567891')
        self.assertEqual(depot_asset_table_data[1].asset_wkn, 'TEST45')
        self.assertEqual(depot_asset_table_data[1].total_nominal, 50)
        self.assertEqual(depot_asset_table_data[1].book_value, 90*50)


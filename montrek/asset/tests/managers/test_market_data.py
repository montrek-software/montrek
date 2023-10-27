from unittest.mock import patch
import pandas as pd
from django.test import TestCase
from asset.tests.factories.asset_factories import (
    AssetStaticSatelliteFactory,
    AssetLiquidSatelliteFactory,
)
from asset.models import AssetHub
from asset.managers.market_data import update_asset_prices
from asset.managers.market_data import get_isin_asset_map
from asset.managers.market_data import get_yf_prices_per_isin

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

    @patch('asset.managers.market_data.yf.download')
    def test_get_yf_prices_per_isin(self, mock_download):
        mock_data_df = self._get_yf_prices_mock_data()
        mock_download.return_value = mock_data_df
        isins_list = ['IE00BYZK4669', 'US0378331005']
        prices_df = get_yf_prices_per_isin(isins_list)
        expected_df = self._dummy_yf_prices_df()
        pd.testing.assert_frame_equal(prices_df, expected_df)

    def test_get_yf_prices_per_isin_no_assets(self):
        isins_list = []
        prices_df = get_yf_prices_per_isin(isins_list)
        self.assertTrue(prices_df.empty)
        self.assertTrue(
            prices_df.columns.tolist() == ['Ticker', 'Close']
        )

    def test_get_yf_prices_per_isin_one_assets(self):
        isins_list = ['IE00BYZK4669']
        prices_df = get_yf_prices_per_isin(isins_list)
        self.assertEqual(len(prices_df), 1)
        self.assertTrue(
            prices_df.columns.tolist() == ['Ticker', 'Close']
        )


    def test_get_market_data(self):
        isin_asset_map = get_isin_asset_map()
        prices_df = self._dummy_yf_prices_df()
        update_asset_prices(isin_asset_map, prices_df)
        prices = [5.94, 166.89]
        for i, asset in enumerate(AssetHub.objects.all()):
            asset_static = asset.asset_static_satellite.last()
            asset_ts = asset.asset_time_series_satellite.all()
            if not asset_static.is_liquid:
                self.assertEqual(asset_ts.count(), 0)
                continue
            self.assertEqual(asset_ts.count(), 1)
            asset_ts = asset_ts.first()
            self.assertAlmostEqual(float(asset_ts.price), prices[i])

    def _get_yf_prices_mock_data(self):
        data = {
            ('Adj Close', 'IE00BYZK4669'): [None, 5.9425],
            ('Adj Close', 'US0378331005'): [166.889999, None],
            ('Close', 'IE00BYZK4669'): [None, 5.9425],
            ('Close', 'US0378331005'): [166.889999, None],
            ('High', 'IE00BYZK4669'): [None, 5.9575],
            ('High', 'US0378331005'): [171.380005, None],
            ('Low', 'IE00BYZK4669'): [None, 5.905],
            ('Low', 'US0378331005'): [165.669998, None],
            ('Open', 'IE00BYZK4669'): [None, 5.905],
            ('Open', 'US0378331005'): [170.369995, None],
            ('Volume', 'IE00BYZK4669'): [None, 9316.0],
            ('Volume', 'US0378331005'): [70345400.0, None]
        }

        index = pd.DatetimeIndex(['2023-10-26', '2023-10-27'], name='Date')
        return pd.DataFrame(data, index=index)

    def _dummy_yf_prices_df(self):
        return pd.DataFrame(
            {'Ticker': ['US0378331005','IE00BYZK4669'],
             'Close': [166.889999, 5.942500]},
            index=pd.DatetimeIndex(['2023-10-26', '2023-10-27'], name='Date')
        )

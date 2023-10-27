import yfinance as yf
import pandas as pd
from typing import Dict
from asset.models import (
    AssetLiquidSatellite,
    AssetTimeSeriesSatellite,
    AssetHub,
)
from baseclasses.repositories import db_helper


def get_isin_asset_map() -> Dict[str, int]:
    return {asset.asset_isin: asset.hub_entity.id  for asset in AssetLiquidSatellite.objects.all()} 


def get_yf_prices_per_isin(isins_list: list) -> pd.DataFrame:
    price_data = yf.download(isins_list, period="1d") 
    price_data = price_data.stack(level=1).rename_axis(['Date', 'Ticker']).reset_index(level=1)
    return price_data.loc[:, ['Ticker','Close']]

def update_asset_prices(isin_asset_map: Dict[str, int], price_data: pd.DataFrame):
    for per_date, row in price_data.iterrows():
        asset_hub = AssetHub.objects.get(id=isin_asset_map[row['Ticker']])
        db_helper.new_satellite_entry(
            AssetTimeSeriesSatellite,
            asset_hub,
            price = row['Close'],
            value_date = per_date
        )


import yfinance as yf
import pandas as pd
from typing import Dict
from asset.models import (
    AssetLiquidSatellite,
    AssetTimeSeriesSatellite,
    AssetHub,
)
from baseclasses.repositories import db_helper


def update_asset_prices_from_yf():
    isin_asset_map = get_isin_asset_map()
    price_data = get_yf_prices_per_isin(list(isin_asset_map.keys()))
    update_asset_prices(isin_asset_map, price_data)

def get_isin_asset_map() -> Dict[str, int]:
    return {asset.asset_isin: asset.hub_entity.id  for asset in AssetLiquidSatellite.objects.all()} 


def get_yf_prices_per_isin(isins_list: list) -> pd.DataFrame:
    if len(isins_list) == 0:
        return pd.DataFrame(columns=['Ticker','Close'])
    price_data = yf.download(isins_list, period="1d") 
    if len(isins_list) == 1:
        price_data['Ticker'] = isins_list[0]
    else:
        price_data = price_data.stack(level=1).rename_axis(['Date', 'Ticker']).reset_index(level=1)
    return price_data.loc[:, ['Ticker','Close']]

def update_asset_prices(isin_asset_map: Dict[str, int], price_data: pd.DataFrame):
    for per_date, row in price_data.iterrows():
        asset_hub = AssetHub.objects.get(id=isin_asset_map[row['Ticker']])
        add_single_price_to_asset(asset_hub, row['Close'], per_date)

def add_single_price_to_asset(asset_hub: AssetHub, price: float, value_date: str):
    db_helper.new_satellite_entry(
        AssetTimeSeriesSatellite,
        asset_hub,
        price = price,
        value_date = value_date
    )

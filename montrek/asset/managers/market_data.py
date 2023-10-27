import yfinance as yf
from typing import Dict
from asset.models import (
    AssetLiquidSatellite,
    AssetTimeSeriesSatellite,
    AssetHub,
)
from baseclasses.repositories import db_helper


def get_isin_asset_map() -> Dict[str, int]:
    return {asset.asset_isin: asset.hub_entity.id  for asset in AssetLiquidSatellite.objects.all()} 

def update_asset_prices(isin_asset_map: Dict[str, int]):
    price_data = yf.download(list(asset_isins.keys()), period="1d") 
    price_data = price_data.stack(level=1).rename_axis(['Date', 'Ticker']).reset_index(level=1)
    price_data = price_data.loc[:, ['Ticker','Close']]
    for per_date, row in price_data.iterrows():
        asset_hub = AssetHub.objects.get(id=asset_isins[row['Ticker']])
        db_helper.new_satellite_entry(
            AssetTimeSeriesSatellite,
            asset_hub,
            price = row['Close'],
            value_date = per_date
        )


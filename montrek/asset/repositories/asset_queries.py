from typing import Tuple
from asset.models import AssetHub
from asset.models import AssetStaticSatellite

def find_asset_hub_by_isin_or_create(
    isin: str,
) -> Tuple[AssetHub, bool]:
    asset_static_sat = AssetStaticSatellite.objects.filter(isin=isin).first()
    if asset_static_sat:
        return asset_static_sat.hub_entity, False
    asset_hub = AssetHub.objects.create()
    AssetStaticSatellite.objects.create(
        hub_entity=asset_hub,
        isin=isin,
    )
    return asset_hub, True

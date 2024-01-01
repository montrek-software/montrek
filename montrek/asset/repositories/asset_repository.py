from asset.models import AssetHub
from asset.models import AssetStaticSatellite
from asset.models import AssetLiquidSatellite
from asset.models import LinkAssetCurrency
from currency.models import CurrencyStaticSatellite
from baseclasses.repositories.montrek_repository import MontrekRepository


class AssetRepository(MontrekRepository):
    hub_class = AssetHub

    def std_queryset(self):
        self.add_satellite_fields_annotations(
            AssetStaticSatellite,
            ["asset_name", "asset_type"],
            self.reference_date,
        )
        self.add_satellite_fields_annotations(
            AssetLiquidSatellite,
            ["asset_isin", "asset_wkn"],
            self.reference_date,
        )
        self.add_linked_satellites_field_annotations(
            CurrencyStaticSatellite,
            LinkAssetCurrency,
            ["ccy_code"],
            self.reference_date,
        )
        return self.build_queryset()

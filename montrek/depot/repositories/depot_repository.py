from baseclasses.repositories.montrek_repository import MontrekRepository
from asset.models import AssetHub, AssetStaticSatellite, AssetLiquidSatellite


class DepotRepository(MontrekRepository):
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
        return self.build_queryset()

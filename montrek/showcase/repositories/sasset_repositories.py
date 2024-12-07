from baseclasses.repositories.montrek_repository import MontrekRepository
from showcase.models.sasset_sat_models import SAssetStaticSatellite, SAssetTypeSatellite
from showcase.models.sasset_hub_models import SAssetHub


class SAssetRepository(MontrekRepository):
    hub_class = SAssetHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(SAssetTypeSatellite, ["asset_type"])
        self.add_satellite_fields_annotations(SAssetStaticSatellite, ["asset_name"])

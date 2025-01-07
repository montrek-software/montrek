from baseclasses.repositories.montrek_repository import MontrekRepository
from showcase.models.sasset_sat_models import SAssetStaticSatellite, SAssetTypeSatellite
from showcase.models.sasset_hub_models import LinkSAssetSCompany, SAssetHub
from showcase.models.scompany_sat_models import SCompanyStaticSatellite


class SAssetRepository(MontrekRepository):
    hub_class = SAssetHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(SAssetTypeSatellite, ["asset_type"])
        self.add_satellite_fields_annotations(SAssetStaticSatellite, ["asset_name"])
        self.add_satellite_fields_annotations(SAssetStaticSatellite, ["asset_isin"])
        self.add_linked_satellites_field_annotations(
            SCompanyStaticSatellite,
            LinkSAssetSCompany,
            ["company_name", "hub_entity_id"],
            rename_field_map={"hub_entity_id": "company_id"},
        )

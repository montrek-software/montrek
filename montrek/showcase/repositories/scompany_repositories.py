from baseclasses.repositories.montrek_repository import MontrekRepository
from mt_economic_common.country.models import CountryStaticSatellite
from showcase.models.scompany_sat_models import SCompanyStaticSatellite
from showcase.models.scompany_hub_models import LinkSCompanyCountry, SCompanyHub


class SCompanyRepository(MontrekRepository):
    hub_class = SCompanyHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            SCompanyStaticSatellite,
            [
                "company_name",
                "company_sector",
            ],
        )
        self.add_linked_satellites_field_annotations(
            CountryStaticSatellite,
            LinkSCompanyCountry,
            ["country_name", "hub_entity_id"],
            rename_field_map={"hub_entity_id": "country_id"},
        )

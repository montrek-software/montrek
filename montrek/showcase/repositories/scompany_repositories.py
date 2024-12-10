from baseclasses.repositories.montrek_repository import MontrekRepository
from showcase.models.scompany_sat_models import SCompanyStaticSatellite
from showcase.models.scompany_hub_models import SCompanyHub


class SCompanyRepository(MontrekRepository):
    hub_class = SCompanyHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            SCompanyStaticSatellite,
            [
                "company_name",
            ],
        )

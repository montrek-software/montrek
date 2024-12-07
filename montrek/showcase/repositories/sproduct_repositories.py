from baseclasses.repositories.montrek_repository import MontrekRepository
from showcase.models.sproduct_hub_models import SProductHub
from showcase.models.sproduct_sat_models import SProductSatellite


class SProductRepository(MontrekRepository):
    hub_class = SProductHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            SProductSatellite,
            [
                "sproduct_name",
                "inception_date",
            ],
        )

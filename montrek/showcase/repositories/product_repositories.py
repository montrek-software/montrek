from baseclasses.repositories.montrek_repository import MontrekRepository
from showcase.models.product_hub_models import ProductHub
from showcase.models.product_sat_models import ProductSatellite


class ProductRepository(MontrekRepository):
    hub_class = ProductHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            ProductSatellite,
            [
                "product_name",
                "inception_date",
            ],
        )

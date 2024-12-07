from django.utils import timezone
from baseclasses.repositories.montrek_repository import MontrekRepository
from showcase.models.sproduct_sat_models import SProductSatellite
from showcase.models.stransaction_sat_models import STransactionSatellite
from showcase.models.stransaction_hub_models import (
    LinkSTransactionSProduct,
    STransactionHub,
)


class STransactionRepository(MontrekRepository):
    hub_class = STransactionHub
    default_order_fields = ("product_name", "value_date")

    def set_annotations(self):
        self.session_data["start_date"] = timezone.datetime.min
        self.session_data["end_date"] = timezone.datetime.max
        self.add_satellite_fields_annotations(
            STransactionSatellite,
            [
                "transaction_external_identifier",
                "transaction_description",
                "transaction_quantity",
                "transaction_price",
            ],
        )
        self.add_linked_satellites_field_annotations(
            SProductSatellite, LinkSTransactionSProduct, ["product_name"]
        )

from django.utils import timezone
from baseclasses.repositories.montrek_repository import MontrekRepository
from showcase.models.product_sat_models import ProductSatellite
from showcase.models.transaction_sat_models import TransactionSatellite
from showcase.models.transaction_hub_models import (
    LinkTransactionProduct,
    TransactionHub,
)


class TransactionRepository(MontrekRepository):
    hub_class = TransactionHub
    default_order_fields = ("product_name", "value_date")

    def set_annotations(self):
        self.session_data["start_date"] = timezone.datetime.min
        self.session_data["end_date"] = timezone.datetime.max
        self.add_satellite_fields_annotations(
            TransactionSatellite,
            [
                "transaction_external_identifier",
                "transaction_description",
                "transaction_quantity",
                "transaction_price",
            ],
        )
        self.add_linked_satellites_field_annotations(
            ProductSatellite, LinkTransactionProduct, ["product_name"]
        )

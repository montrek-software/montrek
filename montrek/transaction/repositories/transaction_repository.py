from django.utils import timezone
from baseclasses.repositories.montrek_repository import MontrekRepository
from transaction.models import TransactionSatellite
from transaction.models import TransactionHub
from transaction.models import TransactionCategorySatellite


class TransactionRepository(MontrekRepository):
    hub_class = TransactionHub

    def std_queryset(self, **kwargs):
        reference_date = timezone.now()
        self.add_satellite_fields_annotations(
            TransactionSatellite,
            [
                "transaction_amount",
                "transaction_price",
                "transaction_date",
                "transaction_party",
                "transaction_party_iban",
                "transaction_description",
            ],
            reference_date,
        )
        self.add_linked_satellites_field_annotations(
            TransactionCategorySatellite,
            "link_transaction_transaction_category",
            ["typename"],
            reference_date,
        )

        self.annotations["transaction_value"] = (
            self.annotations["transaction_amount"]
            * self.annotations["transaction_price"]
        )
        return self.build_queryset()

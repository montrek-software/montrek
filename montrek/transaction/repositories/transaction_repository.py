from django.utils import timezone
from baseclasses.repositories.montrek_repository import MontrekRepository
from transaction.models import TransactionSatellite
from transaction.models import TransactionHub


class TransactionRepository(MontrekRepository):
    hub_class = TransactionHub

    def std_queryset(self, **kwargs):
        reference_date = timezone.now()
        self.add_satellite_fields_annotations(
            TransactionSatellite,
            ["transaction_amount", "transaction_price", "transaction_date"],
            reference_date,
        )
        return self.build_queryset()

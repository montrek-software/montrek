from django.utils import timezone
from baseclasses.repositories.montrek_repository import MontrekRepository
from transaction.models import TransactionCategoryMapHub
from transaction.models import TransactionCategoryMapSatellite

class TransactionCategoryMapRepository(MontrekRepository):
    hub_class = TransactionCategoryMapHub

    def std_queryset(self):
        reference_date = timezone.now()
        self.add_satellite_fields_annotations(
            TransactionCategoryMapSatellite, 
            [
                'field',
                'value',
                'category',
                'is_regex',
            ],
            reference_date)
        return self.build_queryset()

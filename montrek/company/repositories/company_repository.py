from django.utils import timezone
from baseclasses.repositories.montrek_repository import MontrekRepository
from company.models import CompanyHub, CompanyStaticSatellite


class CompanyRepository(MontrekRepository):
    hub_class = CompanyHub

    def std_queryset(self):
        reference_date = timezone.now()
        self.add_satellite_fields_annotations(
            CompanyStaticSatellite, ["company_name", "bloomberg_ticker"], reference_date
        )
        return self.build_queryset()

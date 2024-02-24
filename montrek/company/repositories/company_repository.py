from django.utils import timezone
from baseclasses.repositories.montrek_repository import (
    MontrekRepository,
    paginated_table,
)
from company.models import (
    CompanyHub,
    CompanyStaticSatellite,
    CompanyTimeSeriesSatellite,
)
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)


class CompanyRepository(MontrekRepository):
    hub_class = CompanyHub

    def std_queryset(self):
        reference_date = timezone.now()
        self.add_satellite_fields_annotations(
            CompanyStaticSatellite, ["company_name", "bloomberg_ticker"], reference_date
        )
        return self.build_queryset()

    @paginated_table
    def get_company_table_paginated(self):
        return self.std_queryset()

    @paginated_table
    def get_upload_registry_table_paginated(self):
        return FileUploadRegistryRepository().std_queryset()

    def get_all_time_series(self, company_id):
        return self.build_time_series_queryset(
            CompanyTimeSeriesSatellite, self.reference_date
        )

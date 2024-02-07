from django.utils import timezone
from baseclasses.repositories.montrek_repository import MontrekRepository
from country.models import CountryHub, CountryStaticSatellite


class CountryRepository(MontrekRepository):
    hub_class = CountryHub

    def std_queryset(self):
        reference_date = timezone.now()
        self.add_satellite_fields_annotations(
            CountryStaticSatellite, ["country_name", "country_code"], reference_date
        )
        return self.build_queryset()

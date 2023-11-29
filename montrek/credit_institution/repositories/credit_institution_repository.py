from credit_institution.models import (
    CreditInstitutionHub,
    CreditInstitutionStaticSatellite,
)
from baseclasses.repositories.db_helper import get_satellite_from_hub_query
from baseclasses.repositories.montrek_repository import MontrekRepository


class CreditInstitutionRepository(MontrekRepository):
    def __init__(self, hub_entity_id):
        self._hub_entity = CreditInstitutionHub(pk=hub_entity_id)
        self._static_satellite = get_satellite_from_hub_query(
            self._hub_entity, CreditInstitutionStaticSatellite
        )

    def detail_queryset(self, **kwargs):
        return self._static_satellite

    def table_queryset(self, **kwargs):
        return CreditInstitutionStaticSatellite.objects.all()

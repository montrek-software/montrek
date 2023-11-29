from credit_institution.models import (
    CreditInstitutionHub,
    CreditInstitutionStaticSatellite,
)
from baseclasses.repositories.db_helper import select_satellite
from baseclasses.repositories.montrek_repository import MontrekRepository


class CreditInstitutionRepository(MontrekRepository):
    def __init__(self, hub_entity):
        self._hub_entity = hub_entity
        self._static_satellite = select_satellite(
            self._hub_entity, CreditInstitutionStaticSatellite
        )

    def detail_queryset(self, **kwargs):
        return self._static_satellite

    def table_queryset(self, **kwargs):
        return CreditInstitutionStaticSatellite.objects.all()

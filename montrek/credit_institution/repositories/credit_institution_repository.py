from credit_institution.models import (
    CreditInstitutionHub,
    CreditInstitutionStaticSatellite,
)
from baseclasses.repositories.db_helper import select_satellite


class CreditInstitutionRepository:
    def __init__(self, hub_entity_id):
        self._hub_entity = CreditInstitutionHub.objects.get(id=hub_entity_id)
        self._static_satellite = select_satellite(
            self._hub_entity, CreditInstitutionStaticSatellite
        )

    @property
    def hub_entity(self):
        return self._hub_entity

    @property
    def static_satellite(self):
        return self._static_satellite

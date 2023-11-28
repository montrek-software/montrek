from credit_institution.models import (
    CreditInstitutionHub,
    CreditInstitutionStaticSatellite,
)
from baseclasses.repositories.db_helper import select_satellite


class CreditInstitutionRepository:
    def __init__(self, hub_entity):
        self._hub_entity = hub_entity
        self._static_satellite = select_satellite(
            self._hub_entity, CreditInstitutionStaticSatellite
        )

    @property
    def hub_entity(self):
        return self._hub_entity

    @property
    def static_satellite(self):
        return self._static_satellite

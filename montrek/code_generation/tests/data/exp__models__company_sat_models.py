from django.db import models

from baseclasses.models import MontrekSatelliteABC
from .users.vincentmohiuddin.code.montrek.montrek.code_generation.tests.data.output.models.company_hub_models import (
    CompanyHub,
)


class CompanySatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(CompanyHub, on_delete=models.CASCADE)

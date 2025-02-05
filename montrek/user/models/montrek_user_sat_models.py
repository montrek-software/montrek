from django.db import models

from baseclasses.models import MontrekSatelliteABC
from user.models.montrek_user_hub_models import MontrekUserHub


class MontrekUserSatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(MontrekUserHub, on_delete=models.CASCADE)

from django.db import models

from baseclasses.models import MontrekSatelliteABC
from user.models.montrek_user_hub_models import MontrekUserHub


class MontrekUserSatellite(MontrekSatelliteABC):
    class MontrekUserStatusChoices(models.TextChoices):
        ACTIVE = "active"
        INACTIVE = "inactive"

    hub_entity = models.ForeignKey(MontrekUserHub, on_delete=models.CASCADE)
    montrek_user_status = models.CharField(
        max_length=255,
        choices=MontrekUserStatusChoices.choices,
        default=MontrekUserStatusChoices.INACTIVE,
    )

    identifier_fields = ["hub_entity_id"]

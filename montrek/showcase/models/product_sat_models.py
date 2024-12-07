from django.db import models

from baseclasses.models import MontrekSatelliteABC
from showcase.models.product_hub_models import SProductHub


class SProductSatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(SProductHub, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    inception_date = models.DateField()
    identifier_fields = ["product_name"]

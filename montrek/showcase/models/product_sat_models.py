from django.db import models

from baseclasses.models import MontrekSatelliteABC
from showcase.models.product_hub_models import ProductHub


class ProductSatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(ProductHub, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    inception_date = models.DateField()
    identifier_fields = ["product_name"]

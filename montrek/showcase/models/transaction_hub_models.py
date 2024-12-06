from django.db import models
from baseclasses.fields import HubForeignKey
from baseclasses.models import (
    HubValueDate,
    MontrekHubABC,
    MontrekOneToManyLinkABC,
)
from showcase.models.product_hub_models import ProductHub


class TransactionHub(MontrekHubABC):
    pass


class TransactionHubValueDate(HubValueDate):
    hub = HubForeignKey(TransactionHub)


class LinkTransactionProduct(MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey(TransactionHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(ProductHub, on_delete=models.CASCADE)

from django.db import models
from baseclasses.fields import HubForeignKey
from baseclasses.models import (
    HubValueDate,
    MontrekHubABC,
    MontrekOneToManyLinkABC,
)
from showcase.models.sproduct_hub_models import SProductHub


class STransactionHub(MontrekHubABC):
    pass


class STransactionHubValueDate(HubValueDate):
    hub = HubForeignKey(STransactionHub)


class LinkSTransactionSProduct(MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey(STransactionHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(SProductHub, on_delete=models.CASCADE)

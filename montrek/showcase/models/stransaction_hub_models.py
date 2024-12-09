from django.db import models
from baseclasses.fields import HubForeignKey
from baseclasses.models import (
    HubValueDate,
    MontrekHubABC,
    MontrekOneToManyLinkABC,
)
from showcase.models.sasset_hub_models import SAssetHub
from showcase.models.sproduct_hub_models import SProductHub


class STransactionHub(MontrekHubABC):
    link_stransaction_sproduct = models.ManyToManyField(
        SProductHub,
        through="LinkSTransactionSProduct",
        related_name="link_sproduct_stransaction",
    )
    link_stransaction_sasset = models.ManyToManyField(
        SAssetHub,
        through="LinkSTransactionSAsset",
        related_name="link_sasset_stransaction",
    )


class STransactionHubValueDate(HubValueDate):
    hub = HubForeignKey(STransactionHub)


class LinkSTransactionSProduct(MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey(STransactionHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(SProductHub, on_delete=models.CASCADE)


class LinkSTransactionSAsset(MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey(STransactionHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(SAssetHub, on_delete=models.CASCADE)

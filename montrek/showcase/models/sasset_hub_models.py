from django.db import models
from baseclasses.fields import HubForeignKey
from baseclasses.models import HubValueDate, MontrekHubABC, MontrekOneToManyLinkABC
from showcase.models.scompany_hub_models import SCompanyHub


class SAssetHub(MontrekHubABC):
    link_sasset_scompany = models.ManyToManyField(
        SCompanyHub,
        through="LinkSAssetSCompany",
        related_name="link_scompany_sasset",
    )


class SAssetHubValueDate(HubValueDate):
    hub = HubForeignKey(SAssetHub)


class LinkSAssetSCompany(MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey(SAssetHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(SCompanyHub, on_delete=models.CASCADE)

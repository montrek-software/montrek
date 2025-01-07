from django.db import models
from baseclasses.fields import HubForeignKey
from baseclasses.models import HubValueDate, MontrekHubABC, MontrekOneToManyLinkABC


class SCompanyHub(MontrekHubABC):
    link_scompany_country = models.ManyToManyField(
        "country.CountryHub",
        related_name="link_country_scompany",
        through="LinkSCompanyCountry",
    )


class SCompanyHubValueDate(HubValueDate):
    hub = HubForeignKey(SCompanyHub)


class LinkSCompanyCountry(MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey(SCompanyHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey("country.CountryHub", on_delete=models.CASCADE)

from django.db import models

from baseclasses.fields import HubForeignKey
from baseclasses.models import (
    HubValueDate,
    MontrekHubABC,
    MontrekOneToOneLinkABC,
    MontrekSatelliteABC,
    MontrekTimeSeriesSatelliteABC,
)


class TestMontrekHub(MontrekHubABC):
    pass


class TestHubValueDate(HubValueDate):
    hub = HubForeignKey(TestMontrekHub)


class TestMontrekSatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE)
    identifier_fields = ["test_name", "test_date"]
    test_name = models.CharField(max_length=12)
    test_value = models.CharField(max_length=50, null=True)
    test_text = models.TextField(blank=True)
    test_decimal = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    test_date = models.DateTimeField()


class TestMontrekTimeSeriesSatellite(MontrekTimeSeriesSatelliteABC):
    hub_value_date = models.ForeignKey(TestHubValueDate, on_delete=models.CASCADE)
    test_decimal = models.DecimalField(max_digits=10, decimal_places=4, default=0)


class TestMontrekSatelliteNoIdFields(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE)


class TestLinkHub(MontrekHubABC):
    link_link_hub_test_montrek_hub: models.ManyToManyField = models.ManyToManyField(
        TestMontrekHub,
        related_name="link_test_montrek_hub_link_hub",
        through="LinkTestMontrekTestLink",
    )


class TestLinkSatellite(MontrekSatelliteABC):
    # A custom related_name, unlike TestMontrekSatellite
    hub_entity = models.ForeignKey(
        TestLinkHub, on_delete=models.CASCADE, related_name="test_link_satellites"
    )
    test_id = models.IntegerField(default=0)
    identifier_fields = ["test_id"]


class LinkTestMontrekTestLink(MontrekOneToOneLinkABC):
    hub_in = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(TestLinkHub, on_delete=models.CASCADE)

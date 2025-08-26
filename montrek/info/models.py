from baseclasses.fields import HubForeignKey
from baseclasses.models import (
    HubValueDate,
    MontrekHubABC,
    MontrekOneToManyLinkABC,
    MontrekSatelliteABC,
    MontrekTimeSeriesSatelliteABC,
)
from django.db import models


class TestHubB(MontrekHubABC):
    class Meta:
        managed = False


class TestHubA(MontrekHubABC):
    class Meta:
        managed = False

    link_test_hub_a_test_hub_b = models.ManyToManyField(
        to="TestHubB",
        through="LinkTestHubATestHubB",
        related_name="link_test_hub_b_test_hub_a",
    )


class TestHubValueDateA(HubValueDate):
    hub = HubForeignKey(TestHubA)

    class Meta:
        managed = False


class TestHubValueDateB(HubValueDate):
    hub = HubForeignKey(TestHubB)

    class Meta:
        managed = False


class TestSatA1(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TestHubA, on_delete=models.CASCADE)

    class Meta:
        managed = False


class TestSatA2(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TestHubA, on_delete=models.CASCADE)

    class Meta:
        managed = False


class TestSatB1(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TestHubB, on_delete=models.CASCADE)

    class Meta:
        managed = False


class TestSatB2(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TestHubB, on_delete=models.CASCADE)

    class Meta:
        managed = False


class TestSatTSB1(MontrekTimeSeriesSatelliteABC):
    hub_value_date = models.ForeignKey(TestHubValueDateB, on_delete=models.CASCADE)

    class Meta:
        managed = False


class TestSatTSB2(MontrekTimeSeriesSatelliteABC):
    hub_value_date = models.ForeignKey(TestHubValueDateB, on_delete=models.CASCADE)

    class Meta:
        managed = False


class LinkTestHubATestHubB(MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey("TestHubA", on_delete=models.CASCADE)
    hub_out = models.ForeignKey("TestHubB", on_delete=models.CASCADE)

    class Meta:
        managed = False

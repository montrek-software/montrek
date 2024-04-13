from django.db import models
from django.utils import timezone
from baseclasses.models import (
    DataQualityMixin,
    MontrekHubABC,
    MontrekSatelliteABC,
    MontrekOneToManyLinkABC,
    MontrekOneToOneLinkABC,
    MontrekManyToManyLinkABC,
    MontrekTimeSeriesSatelliteABC,
)

# Create your models here.

####################################################################################################
# Test classes                              / -- LinkHubBHubD -- HubD -- SatD1
#                                          /
#    SatA1 -- HubA -- LinkHubAHubB -- HubB -- SatB1
#    SatA2 -/   \                          \- SatB2
#                \ -- LinkHubAHubC -- HubC -- SatC1
#                                          \- SatTSC2
####################################################################################################


class HubA(MontrekHubABC):
    link_hub_a_hub_b = models.ManyToManyField(
        "HubB", related_name="link_hub_b_hub_a", through="LinkHubAHubB"
    )
    link_hub_a_hub_c = models.ManyToManyField(
        "HubC", related_name="link_hub_c_hub_a", through="LinkHubAHubC"
    )
    link_hub_a_file_upload_registry = models.ManyToManyField(
        "file_upload.FileUploadRegistryHub",
        related_name="link_file_upload_registry_hub_a",
        through="LinkHubAFileUploadRegistry",
    )


class HubB(MontrekHubABC):
    link_hub_b_hub_d = models.ManyToManyField(
        "HubD", related_name="link_hub_d_hub_b", through="LinkHubBHubD"
    )


class HubC(MontrekHubABC):
    pass


class HubD(MontrekHubABC):
    pass


class SatA1(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(HubA, on_delete=models.CASCADE)
    field_a1_str = models.CharField(max_length=50, default="DEFAULT")
    field_a1_int = models.IntegerField(default=0)
    identifier_fields = ["field_a1_str"]


class SatA2(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(HubA, on_delete=models.CASCADE)
    field_a2_str = models.CharField(max_length=50, default="DEFAULT")
    field_a2_float = models.FloatField(default=0.0)
    identifier_fields = ["field_a2_str"]


class SatB1(MontrekSatelliteABC, DataQualityMixin):
    hub_entity = models.ForeignKey(HubB, on_delete=models.CASCADE)
    field_b1_str = models.CharField(max_length=50, default="DEFAULT")
    field_b1_date = models.DateField(default=timezone.now)
    identifier_fields = ["field_b1_str", "field_b1_date", "hub_entity_id"]


class SatB2(MontrekSatelliteABC):
    class ChoiceEnum(models.TextChoices):
        CHOICE1 = "CHOICE1"
        CHOICE2 = "CHOICE2"
        CHOICE3 = "CHOICE3"

    hub_entity = models.ForeignKey(HubB, on_delete=models.CASCADE)
    field_b2_str = models.CharField(max_length=50, default="DEFAULT")
    field_b2_choice = models.CharField(
        max_length=10, choices=ChoiceEnum.choices, default=ChoiceEnum.CHOICE1
    )
    identifier_fields = ["field_b2_str", "hub_entity_id"]


class SatC1(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(HubC, on_delete=models.CASCADE)
    field_c1_str = models.CharField(max_length=50, default="DEFAULT")
    field_c1_bool = models.BooleanField(default=False)
    identifier_fields = ["field_c1_str"]


class SatTSC2(MontrekTimeSeriesSatelliteABC):
    hub_entity = models.ForeignKey(HubC, on_delete=models.CASCADE)
    field_tsc2_float = models.FloatField(default=0.0)


class SatD1(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(HubD, on_delete=models.CASCADE)
    field_d1_str = models.CharField(max_length=50, default="DEFAULT")
    field_d1_int = models.IntegerField(default=0)
    identifier_fields = ["field_d1_str"]


class LinkHubAHubB(MontrekOneToOneLinkABC):
    hub_in = models.ForeignKey(HubA, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(HubB, on_delete=models.CASCADE)


class LinkHubAHubC(MontrekOneToManyLinkABC):
    hub_in = models.ForeignKey(HubA, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(HubC, on_delete=models.CASCADE)


class LinkHubBHubD(MontrekManyToManyLinkABC):
    hub_in = models.ForeignKey(HubB, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(HubD, on_delete=models.CASCADE)


class LinkHubAFileUploadRegistry(MontrekManyToManyLinkABC):
    hub_in = models.ForeignKey(HubA, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(
        "file_upload.FileUploadRegistryHub", on_delete=models.CASCADE
    )

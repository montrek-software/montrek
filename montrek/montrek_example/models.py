from api_upload.models import (
    ApiUploadRegistryHubABC,
    ApiUploadRegistryStaticSatelliteABC,
)
from baseclasses.fields import HubForeignKey
from baseclasses.models import (
    AlertMixin,
    HubValueDate,
    MontrekHubABC,
    MontrekManyToManyLinkABC,
    MontrekOneToManyLinkABC,
    MontrekOneToOneLinkABC,
    MontrekSatelliteABC,
    MontrekTimeSeriesSatelliteABC,
)
from django.db import models
from django.utils import timezone
from file_upload.models import (
    FieldMapHubABC,
    FieldMapStaticSatelliteABC,
    FileUploadRegistryHubABC,
    FileUploadRegistryStaticSatelliteABC,
)

# Create your models here.

####################################################################################################
# Test classes                              / -- LinkHubBHubD -- HubD -- SatD1
#                                          /                      /   \- SatTSD2
#    SatA1 -- HubA -- LinkHubAHubB -- HubB -- SatB1              /
#    SatA2 -/   \                          \- SatB2    LinkHubCHubD
#                \ -- LinkHubAHubC -- HubC -- SatC1   /
#                                          \- SatTSC2/
#                                          \--------/
####################################################################################################


class HubA(MontrekHubABC):
    link_hub_a_hub_b = models.ManyToManyField(
        "HubB", related_name="link_hub_b_hub_a", through="LinkHubAHubB"
    )
    link_hub_a_hub_c = models.ManyToManyField(
        "HubC", related_name="link_hub_c_hub_a", through="LinkHubAHubC"
    )
    link_hub_a_file_upload_registry = models.ManyToManyField(
        "montrek_example.HubAFileUploadRegistryHub",
        related_name="link_file_upload_registry_hub_a",
        through="LinkHubAFileUploadRegistry",
    )
    link_hub_a_api_upload_registry = models.ManyToManyField(
        "HubAApiUploadRegistryHub",
        related_name="link_api_upload_registry_hub_a",
        through="LinkHubAApiUploadRegistry",
    )


class HubB(MontrekHubABC):
    link_hub_b_hub_d = models.ManyToManyField(
        "HubD", related_name="link_hub_d_hub_b", through="LinkHubBHubD"
    )


class HubC(MontrekHubABC):
    link_hub_c_hub_d = models.ManyToManyField(
        "HubD", related_name="link_hub_d_hub_c", through="LinkHubCHubD"
    )


class HubD(MontrekHubABC):
    pass


class AHubValueDate(HubValueDate):
    hub = HubForeignKey(HubA)


class BHubValueDate(HubValueDate):
    hub = HubForeignKey(HubB)


class CHubValueDate(HubValueDate):
    hub = HubForeignKey(HubC)


class DHubValueDate(HubValueDate):
    hub = HubForeignKey(HubD)


class SatA1(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(HubA, on_delete=models.CASCADE)
    field_a1_str = models.CharField(max_length=50, default="DEFAULT")
    field_a1_int = models.IntegerField(default=0)
    identifier_fields = ["field_a1_str"]


class SatA2(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(HubA, on_delete=models.CASCADE)
    field_a2_str = models.CharField(
        max_length=50, default="DEFAULT", null=True, blank=True
    )
    field_a2_float = models.FloatField(default=0.0, null=True, blank=True)
    identifier_fields = ["field_a2_str"]


class SatA3(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(HubA, on_delete=models.CASCADE)
    field_a3_str = models.CharField(
        max_length=50, default="DEFAULT", null=True, blank=True
    )
    field_a3_json = models.JSONField(default=dict)
    identifier_fields = ["field_a3_str"]


class SatB1(MontrekSatelliteABC, AlertMixin):
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
    hub_value_date = models.ForeignKey(CHubValueDate, on_delete=models.CASCADE)
    field_tsc2_float = models.FloatField(default=0.0)


class SatTSC3(MontrekTimeSeriesSatelliteABC):
    hub_value_date = models.ForeignKey(CHubValueDate, on_delete=models.CASCADE)
    field_tsc3_int = models.IntegerField(null=True, blank=True)
    field_tsc3_str = models.CharField(max_length=50, null=True, blank=True)
    field_tsc3_int_times_two = models.GeneratedField(
        expression=models.F("field_tsc3_int") * 2,
        output_field=models.IntegerField(),
        db_persist=True,
    )


class SatTSC4(MontrekTimeSeriesSatelliteABC):
    hub_value_date = models.ForeignKey(CHubValueDate, on_delete=models.CASCADE)
    field_tsc4_int = models.IntegerField(null=True, blank=True)


class SatD1(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(HubD, on_delete=models.CASCADE)
    field_d1_str = models.CharField(max_length=50, default="DEFAULT")
    field_d1_int = models.IntegerField(default=0)
    identifier_fields = ["field_d1_str"]


class SatTSD2(MontrekTimeSeriesSatelliteABC):
    hub_value_date = models.ForeignKey(DHubValueDate, on_delete=models.CASCADE)
    field_tsd2_float = models.FloatField(null=True)
    field_tsd2_int = models.IntegerField(null=True)


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
        "montrek_example.HubAFileUploadRegistryHub", on_delete=models.CASCADE
    )


class LinkHubCHubD(MontrekManyToManyLinkABC):
    hub_in = models.ForeignKey(HubC, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(HubD, on_delete=models.CASCADE)


class HubAFileUploadRegistryHub(FileUploadRegistryHubABC):
    link_file_upload_registry_file_upload_file = models.ManyToManyField(
        "file_upload.FileUploadFileHub",
        related_name="link_file_upload_file_hub_a_file_upload_registry",
        through="LinkHubAFileUploadRegistryFileUploadFile",
    )
    link_file_upload_registry_file_log_file = models.ManyToManyField(
        "file_upload.FileUploadFileHub",
        related_name="link_file_log_file_hub_a_file_upload_registry",
        through="LinkHubAFileUploadRegistryFileLogFile",
    )


class HubAFileUploadRegistryHubValueDate(HubValueDate):
    hub = HubForeignKey(HubAFileUploadRegistryHub)


class LinkHubAFileUploadRegistryFileUploadFile(MontrekOneToOneLinkABC):
    hub_in = models.ForeignKey(
        "montrek_example.HubAFileUploadRegistryHub", on_delete=models.CASCADE
    )
    hub_out = models.ForeignKey(
        "file_upload.FileUploadFileHub", on_delete=models.CASCADE
    )


class LinkHubAFileUploadRegistryFileLogFile(MontrekOneToOneLinkABC):
    hub_in = models.ForeignKey(
        "montrek_example.HubAFileUploadRegistryHub", on_delete=models.CASCADE
    )
    hub_out = models.ForeignKey(
        "file_upload.FileUploadFileHub", on_delete=models.CASCADE
    )


class HubAFileUploadRegistryStaticSatellite(FileUploadRegistryStaticSatelliteABC):
    hub_entity = models.ForeignKey(HubAFileUploadRegistryHub, on_delete=models.CASCADE)


class HubAApiUploadRegistryHub(ApiUploadRegistryHubABC):
    pass


class HubAApiUploadRegistryHubValueDate(HubValueDate):
    hub = HubForeignKey(HubAApiUploadRegistryHub)


class HubAApiUploadRegistryStaticSatellite(ApiUploadRegistryStaticSatelliteABC):
    hub_entity = models.ForeignKey(HubAApiUploadRegistryHub, on_delete=models.CASCADE)


class LinkHubAApiUploadRegistry(MontrekManyToManyLinkABC):
    hub_in = models.ForeignKey(HubA, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(HubAApiUploadRegistryHub, on_delete=models.CASCADE)


class SatA1FieldMapHub(FieldMapHubABC):
    pass


class SatA1FieldMapHubValueDate(HubValueDate):
    hub = HubForeignKey(SatA1FieldMapHub)


class SatA1FieldMapStaticSatellite(FieldMapStaticSatelliteABC):
    hub_entity = models.ForeignKey(SatA1FieldMapHub, on_delete=models.CASCADE)

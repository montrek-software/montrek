import hashlib
from django.db import models
from django.utils import timezone

# Create your models here.


class TimeStampMixin(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class TypeMixin(models.Model):
    class Meta:
        abstract = True

    identifier_fields = ["typename"]
    typename = models.CharField(max_length=50, default="NONE")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


# Base Hub Model ABC
class MontrekHubABC(TimeStampMixin):
    class Meta:
        abstract = True

    identifier = models.CharField(max_length=12, default="")
    is_deleted = models.BooleanField(default=False)


# Base Static Satellite Model ABC
class MontrekSatelliteABC(TimeStampMixin):
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["hash_identifier"]),
            models.Index(fields=["hash_value"]),
        ]

    hub_entity = models.ForeignKey(MontrekHubABC, on_delete=models.CASCADE)
    hash_identifier = models.CharField(max_length=64, default="")
    hash_value = models.CharField(max_length=64, default="")
    state_date_start = models.DateTimeField(
        default=timezone.make_aware(timezone.datetime.min)
    )
    state_date_end = models.DateTimeField(
        default=timezone.make_aware(timezone.datetime.max)
    )

    def save(self, *args, **kwargs):
        if self.hash_identifier == "":
            self._get_hash_identifier()
        if self.hash_value == "":
            self._get_hash_value()
        super().save(*args, **kwargs)

    def _get_hash_identifier(self) -> str:
        if not hasattr(self, "identifier_fields"):
            raise AttributeError(
                f"Satellite {self.__class__.__name__} must have attribute identifier_fields"
            )
        identifier_string = "".join(
            str(getattr(self, field)) for field in self.identifier_fields
        )
        sha256_hash = hashlib.sha256(identifier_string.encode()).hexdigest()
        self.hash_identifier = sha256_hash
        return sha256_hash

    def _get_hash_value(self) -> str:
        exclude_fields = [
            "id",
            "hash_identifier",
            "hash_value",
            "created_at",
            "updated_at",
            "state_date_start",
            "state_date_end",
        ]
        value_fields = [
            field.name
            for field in self._meta.get_fields()
            if field.name not in exclude_fields and not field.is_relation
        ]
        value_string = "".join(str(getattr(self, field)) for field in value_fields)
        sha256_hash = hashlib.sha256(value_string.encode()).hexdigest()
        self.hash_value = sha256_hash
        return sha256_hash

    @property
    def get_hash_identifier(self) -> str:
        return self._get_hash_identifier()

    @property
    def get_hash_value(self) -> str:
        return self._get_hash_value()


class MontrekTimeSeriesSatelliteABC(MontrekSatelliteABC):
    class Meta:
        abstract = True

    value_date = models.DateField()
    identifier_fields = ["value_date"]


class MontrekLinkABC(TimeStampMixin):
    class Meta:
        abstract = True

    hub_in = models.ForeignKey(
        MontrekHubABC, on_delete=models.CASCADE, related_name="in_hub"
    )
    hub_out = models.ForeignKey(
        MontrekHubABC, on_delete=models.CASCADE, related_name="out_hub"
    )
    state_date_start = models.DateTimeField(
        default=timezone.make_aware(timezone.datetime.min)
    )
    state_date_end = models.DateTimeField(
        default=timezone.make_aware(timezone.datetime.max)
    )


# Montrek Test Models


class TestMontrekHub(MontrekHubABC):
    pass


class TestMontrekSatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE)
    identifier_fields = ["test_name"]
    test_name = models.CharField(max_length=12)
    test_value = models.CharField(max_length=50, default="DEFAULT")


class TestMontrekSatelliteNoIdFields(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE)


class TestLinkHub(MontrekHubABC):
    link_link_hub_test_montrek_hub = models.ManyToManyField(
        TestMontrekHub,
        related_name="link_test_montrek_hub_link_hub",
        through="LinkTestMontrekTestLink",
    )


class TestLinkSatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TestLinkHub, on_delete=models.CASCADE)
    test_id = models.IntegerField(default=0)
    identifier_fields = ["test_id"]


class LinkTestMontrekTestLink(MontrekLinkABC):
    hub_in = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(TestLinkHub, on_delete=models.CASCADE)


####################################################################################################
# Test classes
#
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


class HubB(MontrekHubABC):
    pass


class HubC(MontrekHubABC):
    pass


class SatA1(MontrekSatelliteABC):
    hub_entity = HubA
    field_a1_str = models.CharField(max_length=50, default="DEFAULT")
    field_a1_int = models.IntegerField(default=0)
    identifier_fields = ["field_a1_str"]


class SatA2(MontrekSatelliteABC):
    hub_entity = HubA
    field_a2_str = models.CharField(max_length=50, default="DEFAULT")
    field_a2_float = models.FloatField(default=0.0)
    identifier_fields = ["field_a2_str"]


class SatB1(MontrekSatelliteABC):
    hub_entity = HubB
    field_b1_str = models.CharField(max_length=50, default="DEFAULT")
    field_b1_date = models.DateField(default=timezone.now)
    identifier_fields = ["field_b1_str", "field_b1_date"]


class SatB2(MontrekSatelliteABC):
    class ChoiceEnum(models.TextChoices):
        CHOICE1 = "CHOICE1"
        CHOICE2 = "CHOICE2"
        CHOICE3 = "CHOICE3"

    hub_entity = HubB
    field_b2_str = models.CharField(max_length=50, default="DEFAULT")
    field_b2_choice = models.CharField(
        max_length=10, choices=ChoiceEnum.choices, default=ChoiceEnum.CHOICE1
    )
    identifier_fields = ["field_b2_str"]


class SatC1(MontrekSatelliteABC):
    hub_entity = HubC
    field_c1_str = models.CharField(max_length=50, default="DEFAULT")
    field_c1_bool = models.BooleanField(default=False)
    identifier_fields = ["field_c1_str"]


class SatTSC2(MontrekTimeSeriesSatelliteABC):
    hub_entity = HubC
    field_tsc2_float = models.FloatField(default=0.0)


class LinkHubAHubB(MontrekLinkABC):
    hub_in = models.ForeignKey(HubA, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(HubB, on_delete=models.CASCADE)


class LinkHubAHubC(MontrekLinkABC):
    hub_in = models.ForeignKey(HubA, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(HubC, on_delete=models.CASCADE)

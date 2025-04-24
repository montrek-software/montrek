import datetime
import hashlib
from enum import Enum

from django.conf import settings
from django.db import models
from django.utils import timezone

from baseclasses.dataclasses.alert import AlertEnum
from baseclasses.fields import HubForeignKey
from baseclasses.utils import datetime_to_montrek_time

# Create your models here.


class TimeStampMixin(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class StateMixin(models.Model):
    class Meta:
        abstract = True

    state_date_start = models.DateTimeField(
        default=timezone.make_aware(timezone.datetime.min)
    )
    state_date_end = models.DateTimeField(
        default=timezone.make_aware(timezone.datetime.max)
    )
    comment = models.CharField(max_length=255, default="", blank=True)


class UserMixin(models.Model):
    class Meta:
        abstract = True

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name="%(class)s",
        null=True,
    )


class AlertMixin(models.Model):
    class Meta:
        abstract = True

    ALERT_CHOICES = [
        (status.value.description, status.value.description) for status in AlertEnum
    ]

    alert_level = models.CharField(
        max_length=10,
        choices=ALERT_CHOICES,
        default=AlertEnum.OK.value.description,
    )
    alert_message = models.CharField(max_length=255, null=True, blank=True)


class ValueDateList(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["value_date"]),
        ]

    value_date = models.DateField(unique=True, null=True, blank=True)

    def __str__(self):
        return f"value_date: {self.value_date}"


# Base Hub Model ABC
class MontrekHubABC(TimeStampMixin, StateMixin, UserMixin):
    class Meta:
        abstract = True

    identifier = models.CharField(max_length=12, default="")

    def get_hub_value_date(self):
        return self.hub_value_date.get(value_date_list__value_date=None)

    def __str__(self):
        sat_class = None
        related_sat_classes = [
            r.related_model
            for r in self._meta.related_objects
            if issubclass(r.related_model, MontrekSatelliteABC)
        ]
        for sat_class in related_sat_classes:
            id_field = sat_class.identifier_fields[0]
            if id_field == "hub_entity_id":
                continue
            sat = (
                getattr(self, sat_class.__name__.lower() + "_set")
                .order_by("-state_date_end")
                .first()
            )
            if not sat:
                continue
            return getattr(sat, id_field)
        return super().__str__()


class HubValueDate(models.Model):
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["value_date_list"]),
            models.Index(fields=["hub"]),
        ]

    hub = HubForeignKey(MontrekHubABC)
    value_date_list = models.ForeignKey(ValueDateList, on_delete=models.CASCADE)

    def __str__(self):
        return f"hub: {self.hub} value_date_list: {self.value_date_list}"


# Base Static Satellite Model ABC
class MontrekSatelliteBaseABC(TimeStampMixin, StateMixin, UserMixin):
    class Meta:
        abstract = True

    hash_identifier = models.CharField(max_length=64, default="")
    hash_value = models.CharField(max_length=64, default="")

    identifier_fields = []

    # Some hubs can have multiple satellites (e.g. timeseries).
    allow_multiple = False
    is_timeseries = False

    def save(self, *args, **kwargs):
        if self.hash_identifier == "":
            self._get_hash_identifier()
        if self.hash_value == "":
            self._get_hash_value()
        super().save(*args, **kwargs)

    def _get_hash_identifier(self) -> str:
        if len(self.identifier_fields) == 0:
            raise AttributeError(
                f"Satellite {self.__class__.__name__} must have property identifier_fields"
            )
        identifier_string = self._get_identifier_string()
        sha256_hash = hashlib.sha256(identifier_string.encode()).hexdigest()
        self.hash_identifier = sha256_hash
        return sha256_hash

    def _get_hash_value(self) -> str:
        value_string = self._get_value_string()
        sha256_hash = hashlib.sha256(value_string.encode()).hexdigest()
        self.hash_value = sha256_hash
        return sha256_hash

    def _get_identifier_string(self):
        identifier_string = ""
        for field in self.identifier_fields:
            value = getattr(self, field)
            if isinstance(value, (datetime.datetime)):
                value = datetime_to_montrek_time(value)
            identifier_string += str(value)
        return identifier_string

    def _get_value_string(self):
        value_fields = self.get_value_field_names()
        value_string = ""
        for field in value_fields:
            if field in self.exclude_from_hash_value():
                continue
            value = getattr(self, field)
            if isinstance(value, (datetime.datetime)):
                value = datetime_to_montrek_time(value)
            value_string += str(value)
            # TODO: Handle decimal here
        return value_string

    @classmethod
    def exclude_fields(cls) -> list[str]:
        exclude_fields = [
            "id",
            "hash_identifier",
            "hash_value",
            "created_at",
            "updated_at",
            "state_date_start",
            "state_date_end",
            "created_by",
        ]
        return exclude_fields

    @classmethod
    def exclude_from_hash_value(cls) -> list[str]:
        return ["comment"]

    @classmethod
    def get_value_field_names(cls) -> list[str]:
        value_fields = [field.name for field in cls.get_value_fields()]
        return value_fields

    @classmethod
    def get_value_fields(cls) -> list[str]:
        value_fields = [
            field
            for field in cls._meta.get_fields()
            if field.name not in cls.exclude_fields()
            and not field.is_relation
            and not isinstance(field, models.GeneratedField)
        ]
        return value_fields

    @classmethod
    def get_field_names(cls) -> list[str]:
        field_names = [field.name for field in cls._meta.get_fields()]
        return field_names

    @property
    def get_hash_identifier(self) -> str:
        return self._get_hash_identifier()

    @property
    def get_hash_value(self) -> str:
        return self._get_hash_value()

    def __str__(self) -> str:
        return ",".join(
            [f"{field} -> {getattr(self, field)}" for field in self.identifier_fields]
        )


class MontrekSatelliteABC(MontrekSatelliteBaseABC):
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["hash_identifier"]),
            models.Index(fields=["hash_value"]),
            models.Index(fields=["hub_entity"]),
        ]

    hub_entity = models.ForeignKey(MontrekHubABC, on_delete=models.CASCADE)

    @classmethod
    def get_related_hub_class(cls) -> type[MontrekHubABC]:
        return cls.hub_entity.field.related_model

    def get_hub_value_date(self) -> HubValueDate:
        return self.hub_entity.get_hub_value_date()


class MontrekTimeSeriesSatelliteABC(MontrekSatelliteBaseABC):
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["hash_identifier"]),
            models.Index(fields=["hash_value"]),
            models.Index(fields=["hub_value_date"]),
        ]

    hub_value_date = models.ForeignKey(HubValueDate, on_delete=models.CASCADE)
    value_date = models.DateField()
    allow_multiple = True
    is_timeseries = True
    identifier_fields = ["hub_value_date_id"]

    @classmethod
    def get_related_hub_class(cls) -> type[MontrekHubABC]:
        return cls.hub_value_date.field.related_model.hub.field.related_model


class MontrekTypeSatelliteABC(MontrekSatelliteABC):
    class Meta:
        abstract = True

    typename = models.CharField(max_length=50, default="NONE")
    identifier_fields = ["typename"]


class LinkTypeEnum(Enum):
    NONE = 0
    ONE_TO_ONE = 1
    ONE_TO_MANY = 2
    MANY_TO_MANY = 3


class MontrekLinkABC(TimeStampMixin, StateMixin):
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["hub_in"]),
            models.Index(fields=["hub_out"]),
        ]

    link_type = LinkTypeEnum.NONE
    hub_in = models.ForeignKey(
        MontrekHubABC, on_delete=models.CASCADE, related_name="in_hub"
    )
    hub_out = models.ForeignKey(
        MontrekHubABC, on_delete=models.CASCADE, related_name="out_hub"
    )

    def __str__(self) -> str:
        return f"{self.hub_in.identifier or self.hub_in.pk} -> {self.hub_out.identifier or self.hub_out.pk}"

    @classmethod
    def get_related_hub_class(cls, hub_field: str) -> type[MontrekHubABC]:
        return getattr(cls, hub_field).field.related_model


class MontrekOneToOneLinkABC(MontrekLinkABC):
    class Meta:
        abstract = True

    link_type = LinkTypeEnum.ONE_TO_ONE


class MontrekOneToManyLinkABC(MontrekLinkABC):
    class Meta:
        abstract = True

    link_type = LinkTypeEnum.ONE_TO_MANY


class MontrekManyToManyLinkABC(MontrekLinkABC):
    class Meta:
        abstract = True

    link_type = LinkTypeEnum.MANY_TO_MANY


# Montrek Test Models

# TODO: Remove these models and factories and rewrite tests to use the new models


class TestMontrekHub(MontrekHubABC):
    pass


class TestHubValueDate(HubValueDate):
    hub = HubForeignKey(TestMontrekHub)


class TestMontrekSatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE)
    identifier_fields = ["test_name", "test_date"]
    test_name = models.CharField(max_length=12)
    test_value = models.CharField(max_length=50, null=True)
    test_decimal = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    test_date = models.DateTimeField()


class TestMontrekTimeSeriesSatellite(MontrekTimeSeriesSatelliteABC):
    hub_value_date = models.ForeignKey(TestHubValueDate, on_delete=models.CASCADE)
    test_decimal = models.DecimalField(max_digits=10, decimal_places=4, default=0)


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


class LinkTestMontrekTestLink(MontrekOneToOneLinkABC):
    hub_in = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(TestLinkHub, on_delete=models.CASCADE)

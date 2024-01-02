import hashlib
import datetime
from typing import List
from enum import Enum
from django.db import models
from django.utils import timezone
from baseclasses.utils import datetime_to_montrek_time

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


class StateDateMixin(models.Model):
    class Meta:
        abstract = True

    state_date_start = models.DateTimeField(
        default=timezone.make_aware(timezone.datetime.min)
    )
    state_date_end = models.DateTimeField(
        default=timezone.make_aware(timezone.datetime.max)
    )


# Base Hub Model ABC
class MontrekHubABC(TimeStampMixin, StateDateMixin):
    class Meta:
        abstract = True

    identifier = models.CharField(max_length=12, default="")
    is_deleted = models.BooleanField(default=False)


# Base Static Satellite Model ABC
class MontrekSatelliteABC(TimeStampMixin, StateDateMixin):
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["hash_identifier"]),
            models.Index(fields=["hash_value"]),
        ]

    hub_entity = models.ForeignKey(MontrekHubABC, on_delete=models.CASCADE)
    hash_identifier = models.CharField(max_length=64, default="")
    hash_value = models.CharField(max_length=64, default="")

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
            value = getattr(self, field)
            if isinstance(value, (datetime.datetime)):
                value = datetime_to_montrek_time(value)
            value_string += str(value)
        return value_string


    @classmethod
    def exclude_fields(self) -> List[str]:
        exclude_fields = [
            "id",
            "hash_identifier",
            "hash_value",
            "created_at",
            "updated_at",
            "state_date_start",
            "state_date_end",
        ]
        return exclude_fields

    @classmethod
    def get_value_field_names(cls) -> List[str]:
        value_fields = [field.name for field in cls.get_value_fields()]
        return value_fields

    @classmethod
    def get_value_fields(cls) -> List[str]:
        value_fields = [
            field
            for field in cls._meta.get_fields()
            if field.name not in cls.exclude_fields() and not field.is_relation
        ]
        return value_fields

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


class LinkTypeEnum(Enum):
    NONE = 0
    ONE_TO_ONE = 1
    ONE_TO_MANY = 2
    MANY_TO_MANY = 3


class MontrekLinkABC(TimeStampMixin, StateDateMixin):
    class Meta:
        abstract = True

    link_type = LinkTypeEnum.NONE
    hub_in = models.ForeignKey(
        MontrekHubABC, on_delete=models.CASCADE, related_name="in_hub"
    )
    hub_out = models.ForeignKey(
        MontrekHubABC, on_delete=models.CASCADE, related_name="out_hub"
    )


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


class LinkTestMontrekTestLink(MontrekOneToOneLinkABC):
    hub_in = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(TestLinkHub, on_delete=models.CASCADE)

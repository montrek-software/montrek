import hashlib
from typing import List
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
        value_fields = self.get_value_fields()
        value_string = "".join(str(getattr(self, field)) for field in value_fields)
        sha256_hash = hashlib.sha256(value_string.encode()).hexdigest()
        self.hash_value = sha256_hash
        return sha256_hash

    @classmethod
    def get_value_fields(self) -> List[str]:
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


class LinkTestMontrekTestLink(MontrekLinkABC):
    hub_in = models.ForeignKey(TestMontrekHub, on_delete=models.CASCADE)
    hub_out = models.ForeignKey(TestLinkHub, on_delete=models.CASCADE)

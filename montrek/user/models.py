from typing import ClassVar

from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

from baseclasses.fields import HubForeignKey
from baseclasses.models import HubValueDate, MontrekHubABC, MontrekSatelliteABC


class MontrekUserManager(BaseUserManager):
    # Keyword-only: Django's UserManager takes the username first, and a caller
    # written for it (mozilla-django-oidc, say) would set that as the password.
    def create_user(self, *, password=None, **extra_fields):
        email = extra_fields.get("email")
        if not email:
            raise ValueError("User must have an email address.")
        extra_fields.pop("email")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        user = self.create_user(email=email, password=password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class MontrekUser(AbstractUser):
    username = None  # type: ignore[assignment]  # removes AbstractUser.username (documented Django pattern)
    email = models.EmailField(("email address"), unique=True)
    # Who the user is at the OpenID provider: its issuer and the user's subject
    # there (the sub claim). Set at the first sign-in through the provider, by
    # email; from then on the user is matched by these, not by email, which
    # the provider may let its users change.
    oidc_issuer = models.CharField(max_length=255, blank=True, default="")
    oidc_subject = models.CharField(max_length=255, blank=True, default="")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[MontrekUserManager] = MontrekUserManager()  # type: ignore[assignment]  # email based, replaces the username based UserManager

    class Meta(AbstractUser.Meta):  # type: ignore[name-defined]  # django-stubs does not declare the model's Meta
        constraints = [
            models.UniqueConstraint(
                fields=["oidc_issuer", "oidc_subject"],
                condition=~models.Q(oidc_subject=""),
                name="unique_oidc_subject",
            )
        ]

    def __str__(self):
        return self.email


class UserAssignmentHub(MontrekHubABC):
    def __str__(self):
        sat = (
            self.userassignmentsatellite_set.select_related("user")
            .order_by("-state_date_end")
            .first()
        )
        if sat and sat.user_id:
            return str(sat.user)
        return super().__str__()


class UserAssignmentHubValueDate(HubValueDate):
    hub = HubForeignKey(UserAssignmentHub)


class UserAssignmentSatellite(MontrekSatelliteABC):
    hub_entity = models.ForeignKey(UserAssignmentHub, on_delete=models.CASCADE)
    # Indexed by the unique constraint
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_assignment_satellites",
        db_index=False,
    )

    identifier_fields = ["user_id"]

    class Meta:
        indexes = [
            models.Index(fields=["hash_identifier"]),
            models.Index(fields=["hash_value"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                name="unique_user_assignment_satellite_per_user",
            )
        ]

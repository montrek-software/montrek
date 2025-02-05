from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

from user.models.montrek_user_sat_models import MontrekUserSatellite
from user.repositories.montrek_user_repositories import MontrekUserRepository


class MontrekUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("User must have an email address.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class MontrekUser(AbstractUser):
    username = None
    email = models.EmailField(("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = MontrekUserManager()

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            self.is_active = False
        super().save(*args, **kwargs)
        if is_new:
            session_data = {"user_id": self.pk}
            montrek_user_sat_data = {
                "montrek_user_status": MontrekUserSatellite.MontrekUserStatusChoices.INACTIVE.value,
            }
            MontrekUserRepository(session_data).create_by_dict(montrek_user_sat_data)

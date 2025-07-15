from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class MontrekUserManager(BaseUserManager):
    def create_user(self, password=None, **extra_fields):
        email = extra_fields.get("email")
        if not email:
            raise ValueError("User must have an email address.")
        extra_fields.pop("email")
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

from django.contrib.auth.models import AbstractUser, BaseUserManager

class MontrekUserManager(BaseUserManager):
    pass


class MontrekUser(AbstractUser):
    objects = MontrekUserManager()


from django.contrib.auth.models import AbstractUser, UserManager

class MontrekUserManager(UserManager):
    pass


class MontrekUser(AbstractUser):
    objects = MontrekUserManager()


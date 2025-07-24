from django.conf import settings
from django.contrib.auth import get_user_model


def run():
    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        raise EnvironmentError("No ADMIN_EMAIL, ADMIN_PASSWORD set")
    User = get_user_model()
    User.objects.create_superuser(settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD)

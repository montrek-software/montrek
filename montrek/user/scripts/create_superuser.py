from django.conf import settings


def run():
    print(settings.ADMIN_NAME)
    if (
        not settings.ADMIN_NAME
        or not settings.ADMIN_EMAIL
        or not settings.ADMIN_PASSWORD
    ):
        raise EnvironmentError("No ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD set")

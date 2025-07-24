import logging

from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


def run():
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD
    if not admin_email or not admin_password:
        raise EnvironmentError("No ADMIN_EMAIL, ADMIN_PASSWORD set")
    User = get_user_model()
    if not User.objects.filter(email=admin_email).exists():
        User.objects.create_superuser(admin_email, admin_password)
        logger.info(f"Created admin {admin_email}")
    else:
        logger.info(f"Admin {admin_email} exists.")

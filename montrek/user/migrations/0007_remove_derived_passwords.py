import base64
import hashlib

from django.contrib.auth.hashers import (
    UNUSABLE_PASSWORD_PREFIX,
    check_password,
    make_password,
)
from django.db import migrations


def derived_password(email: str) -> str:
    # The username mozilla-django-oidc derives from the email (its
    # default_username_algo), which users it created were given as their
    # password. Spelled out here so the migration does not depend on the library.
    # Not a security use of SHA-1: it only reproduces the library's value.
    digest = hashlib.sha1(email.encode("utf-8"), usedforsecurity=False).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def remove_derived_passwords(apps, schema_editor):
    user_model = apps.get_model("user", "MontrekUser")
    unusable = make_password(None)
    for user in user_model.objects.exclude(
        password__startswith=UNUSABLE_PASSWORD_PREFIX
    ).only("pk", "email", "password"):
        # The provider may have sent the email in other case than montrek
        # stores it.
        candidates = {user.email, user.email.lower()}
        if any(check_password(derived_password(c), user.password) for c in candidates):
            user.password = unusable
            user.save(update_fields=["password"])


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0006_add_value_date_copy"),
    ]

    operations = [
        migrations.RunPython(remove_derived_passwords, migrations.RunPython.noop),
    ]

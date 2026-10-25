"""Encrypted model fields take their key from FIELD_ENCRYPTION_KEY.

django-fernet-encrypted-fields derives the Fernet key from SECRET_KEY (with
SALT_KEY as the salt), which ties every encrypted value in the database to the
key that also signs sessions. Here the derivation reads FIELD_ENCRYPTION_KEY
instead, for both, so the field key can be kept with the backups and
SECRET_KEY can be replaced on its own.

FIELD_ENCRYPTION_KEY defaults to SECRET_KEY, and the package used to get
SALT_KEY = SECRET_KEY, so an install that does not set it derives the same key
as before and reads its existing data unchanged.
"""

import base64

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.utils.functional import cached_property
from encrypted_fields.fields import EncryptedFieldMixin

# The package's own derivation, kept for the test that both agree on an install
# without FIELD_ENCRYPTION_KEY.
PACKAGE_KEYS = EncryptedFieldMixin.__dict__["keys"]


def derive_fernet_key(field_key: str) -> bytes:
    # The package's derivation, with the field key as password and salt.
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=field_key.encode("utf-8"),
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(field_key.encode("utf-8")))


def _keys(self) -> list[bytes]:
    return [derive_fernet_key(settings.FIELD_ENCRYPTION_KEY)]


def use_field_encryption_key() -> None:
    """Replaces the package's key derivation; called from BaseclassesConfig.ready()."""
    keys = cached_property(_keys)
    keys.__set_name__(EncryptedFieldMixin, "keys")
    EncryptedFieldMixin.keys = keys  # type: ignore[assignment]

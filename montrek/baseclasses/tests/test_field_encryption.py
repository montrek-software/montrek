"""Encrypted fields read FIELD_ENCRYPTION_KEY, not SECRET_KEY.

Each test builds its own field: a field caches its key on first use, so one
created under different settings would keep the old key.
"""

from django.test import SimpleTestCase, override_settings
from encrypted_fields import EncryptedCharField

from baseclasses.field_encryption import PACKAGE_KEYS

OLD_SECRET_KEY = "old-secret-key"  # noqa: S105 # nosec: B105
NEW_SECRET_KEY = "new-secret-key"  # noqa: S105 # nosec: B105
FIELD_KEY = "field-key"


def encrypt(value):
    return EncryptedCharField().get_prep_value(value)


def decrypt(token):
    return EncryptedCharField().to_python(token)


class TestFieldEncryptionKey(SimpleTestCase):
    @override_settings(
        SECRET_KEY=OLD_SECRET_KEY,
        SALT_KEY=OLD_SECRET_KEY,
        FIELD_ENCRYPTION_KEY=OLD_SECRET_KEY,
    )
    def test_same_key_as_the_package_while_the_field_key_is_the_secret_key(self):
        field = EncryptedCharField()
        self.assertEqual(field.keys, PACKAGE_KEYS.func(field))

    def test_data_encrypted_before_the_split_stays_readable(self):
        with override_settings(
            SECRET_KEY=OLD_SECRET_KEY, FIELD_ENCRYPTION_KEY=OLD_SECRET_KEY
        ):
            token = encrypt("sftp-password")
        # The install sets FIELD_ENCRYPTION_KEY to its old SECRET_KEY, then
        # replaces SECRET_KEY.
        with override_settings(
            SECRET_KEY=NEW_SECRET_KEY, FIELD_ENCRYPTION_KEY=OLD_SECRET_KEY
        ):
            self.assertEqual(decrypt(token), "sftp-password")

    def test_secret_key_does_not_change_the_field_key(self):
        with override_settings(
            SECRET_KEY=OLD_SECRET_KEY, FIELD_ENCRYPTION_KEY=FIELD_KEY
        ):
            token = encrypt("sftp-password")
        with override_settings(
            SECRET_KEY=NEW_SECRET_KEY, FIELD_ENCRYPTION_KEY=FIELD_KEY
        ):
            self.assertEqual(decrypt(token), "sftp-password")

    def test_another_field_key_cannot_decrypt(self):
        with override_settings(FIELD_ENCRYPTION_KEY=FIELD_KEY):
            token = encrypt("sftp-password")
        with override_settings(FIELD_ENCRYPTION_KEY="another-field-key"):
            # The package hands back the token when decryption fails.
            self.assertEqual(decrypt(token), token)

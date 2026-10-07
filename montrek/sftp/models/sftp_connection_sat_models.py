from django.db import models
from encrypted_fields import EncryptedCharField, EncryptedTextField

from baseclasses.models import MontrekSatelliteABC
from sftp.models.sftp_connection_hub_models import SftpConnectionHub
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator


class SftpConnectionSatellite(MontrekSatelliteABC):
    """Non-sensitive connection settings."""

    hub_entity = models.ForeignKey(SftpConnectionHub, on_delete=models.CASCADE)

    host = models.CharField(max_length=253)
    port = models.PositiveIntegerField(
        default=22,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
    )
    user = models.CharField(max_length=128)

    host_key_fingerprint = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="Expected server key, e.g. 'SHA256:abc…'. Empty = no verification.",
    )
    base_path = models.CharField(max_length=1024, blank=True, default="/")
    timeout_seconds = models.PositiveSmallIntegerField(default=30)

    identifier_fields = ["host", "port", "user"]

    def __str__(self):
        return f"{self.user}@{self.host}:{self.port}"


class SftpCredentialSatellite(MontrekSatelliteABC):
    """Secrets for an SFTP connection; rotates independently of the settings."""

    class AuthMethod(models.TextChoices):
        PASSWORD = "password", "Password"
        PRIVATE_KEY = "private_key", "Private key"

    hub_entity = models.ForeignKey(SftpConnectionHub, on_delete=models.CASCADE)

    auth_method = models.CharField(
        max_length=16, choices=AuthMethod.choices, default=AuthMethod.PASSWORD
    )
    # Empty values are stored as NULL by encrypted_fields, hence null=True
    password = EncryptedCharField(null=True, blank=True)
    private_key = EncryptedTextField(null=True, blank=True)
    private_key_passphrase = EncryptedCharField(null=True, blank=True)

    identifier_fields = ["hub_entity_id"]

    def clean(self):
        super().clean()
        if self.auth_method == self.AuthMethod.PASSWORD and not self.password:
            raise ValidationError({"password": "Required for password authentication."})
        if self.auth_method == self.AuthMethod.PRIVATE_KEY and not self.private_key:
            raise ValidationError({"private_key": "Required for key authentication."})

    def __str__(self):
        # Never render secrets, e.g. in the admin, logs or tracebacks
        return f"Credentials ({self.get_auth_method_display()}) for hub {self.hub_entity_id}"

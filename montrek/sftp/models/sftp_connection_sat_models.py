from django.db import models
from encrypted_fields import EncryptedCharField, EncryptedTextField

from baseclasses.models import MontrekSatelliteABC
from sftp.models.sftp_connection_hub_models import SftpConnectionHub
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)

# The SHA256 fingerprint as OpenSSH prints it: 43 base64 characters
host_key_fingerprint_validator = RegexValidator(
    r"^(SHA256:)?[A-Za-z0-9+/]{43}=?$",
    "Enter the SHA256 fingerprint of the host key, e.g. 'SHA256:abc…'.",
)


class SftpConnectionSatellite(MontrekSatelliteABC):
    """Non-sensitive connection settings."""

    hub_entity = models.ForeignKey(SftpConnectionHub, on_delete=models.CASCADE)

    host = models.CharField(max_length=253)
    port = models.PositiveIntegerField(
        default=22,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
    )
    user = models.CharField(max_length=128)

    # Required unless trusted_host: without it a man-in-the-middle could pose as
    # the server and receive the credentials
    host_key_fingerprint = models.CharField(
        max_length=128,
        blank=True,
        default="",
        validators=[host_key_fingerprint_validator],
        help_text=(
            "SHA256 fingerprint of the server's host key, e.g. 'SHA256:abc…'. "
            "Get it from the server's operator, or verify the output of "
            "'ssh-keyscan -p <port> <host> | ssh-keygen -lf -' with them."
        ),
    )
    trusted_host = models.BooleanField(
        default=False,
        help_text=(
            "Connect without a host key fingerprint. Only for test servers: "
            "anyone who can intercept the connection can then pose as the "
            "server and receive the credentials."
        ),
    )
    base_path = models.CharField(max_length=1024, blank=True, default="/")
    timeout_seconds = models.PositiveSmallIntegerField(default=30)

    identifier_fields = ["host", "port", "user"]

    def clean(self):
        super().clean()
        if not self.trusted_host and not self.host_key_fingerprint:
            raise ValidationError(
                {"host_key_fingerprint": "Required unless the host is trusted."}
            )

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

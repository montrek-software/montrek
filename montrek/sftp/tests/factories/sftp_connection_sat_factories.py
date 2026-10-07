import factory
from baseclasses.tests.factories.montrek_factory_schemas import (
    MontrekSatelliteFactory,
)

from sftp.tests.factories.sftp_connection_hub_factories import SftpConnectionHubFactory
from sftp.models.sftp_connection_sat_models import (
    SftpConnectionSatellite,
    SftpCredentialSatellite,
)

# Test-only secrets, defined once so the scanners need a single exemption each
TEST_PASSWORD = "s3cr3t-password"  # nosec B105 # noqa: S105 : test-only password
TEST_OLD_PASSWORD = "old-password"  # nosec B105 # noqa: S105 : test-only password
TEST_PASSPHRASE = "key-passphrase"  # nosec B105 # noqa: S105 : test-only password
TEST_PRIVATE_KEY = (
    "-----BEGIN OPENSSH PRIVATE KEY-----\n"  # gitleaks:allow : test-only dummy key
    "dGVzdC1rZXk=\n"
    "-----END OPENSSH PRIVATE KEY-----\n"
)

# Public data, not a secret: what a server's host key hashes to
TEST_HOST_FINGERPRINT = "SHA256:XqPhvw9Gx9FBbCQvXZdx/BZTS5dQfeYFHW6/ie12Kp8"


class SftpConnectionSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = SftpConnectionSatellite

    hub_entity = factory.SubFactory(SftpConnectionHubFactory)
    host = factory.Sequence(lambda n: f"sftp{n}.example.com")
    port = 22
    user = factory.Faker("user_name")
    host_key_fingerprint = TEST_HOST_FINGERPRINT
    base_path = "/upload"
    timeout_seconds = 30


class SftpCredentialSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = SftpCredentialSatellite

    hub_entity = factory.SubFactory(SftpConnectionHubFactory)
    auth_method = SftpCredentialSatellite.AuthMethod.PASSWORD
    password = factory.Faker("password")


class SftpPrivateKeyCredentialSatelliteFactory(MontrekSatelliteFactory):
    class Meta:
        model = SftpCredentialSatellite

    hub_entity = factory.SubFactory(SftpConnectionHubFactory)
    auth_method = SftpCredentialSatellite.AuthMethod.PRIVATE_KEY
    private_key = TEST_PRIVATE_KEY
    private_key_passphrase = factory.Faker("password")

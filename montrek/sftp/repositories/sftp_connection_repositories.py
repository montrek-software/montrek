from baseclasses.repositories.montrek_repository import MontrekRepository
from sftp.models.sftp_connection_hub_models import SftpConnectionHub
from sftp.models.sftp_connection_sat_models import (
    SftpConnectionSatellite,
    SftpCredentialSatellite,
)


class SftpConnectionRepository(MontrekRepository):
    hub_class = SftpConnectionHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            SftpConnectionSatellite,
            [
                "host",
                "port",
                "user",
                "host_key_fingerprint",
                "base_path",
                "timeout_seconds",
            ],
        )
        self.add_satellite_fields_annotations(
            SftpCredentialSatellite,
            ["auth_method", "password", "private_key", "private_key_passphrase"],
        )

from django.core.exceptions import ValidationError
from django.db.models import Model

from baseclasses.forms import MontrekCreateForm
from sftp.models.sftp_connection_sat_models import (
    SftpConnectionSatellite,
    SftpCredentialSatellite,
)


class SftpConnectionCreateForm(MontrekCreateForm):
    def clean(self):
        # super() restores secrets left blank on update, so the checks see the
        # values that will actually be stored
        cleaned_data = super().clean()
        # A malformed fingerprint is already reported by its own validator
        if "host_key_fingerprint" not in self.errors:
            self._clean_model(
                SftpConnectionSatellite(
                    host_key_fingerprint=cleaned_data.get("host_key_fingerprint"),
                    trusted_host=cleaned_data.get("trusted_host"),
                )
            )
        self._clean_model(
            SftpCredentialSatellite(
                auth_method=cleaned_data.get("auth_method"),
                password=cleaned_data.get("password"),
                private_key=cleaned_data.get("private_key"),
            )
        )
        return cleaned_data

    def _clean_model(self, instance: Model) -> None:
        """Apply the model's own cross-field rules, so they live in one place."""
        try:
            instance.clean()
        except ValidationError as error:
            self.add_error(None, error)

from django.core.exceptions import ValidationError

from baseclasses.forms import MontrekCreateForm
from sftp.models.sftp_connection_sat_models import SftpCredentialSatellite


class SftpConnectionCreateForm(MontrekCreateForm):
    def clean(self):
        # super() restores secrets left blank on update, so the check sees the
        # values that will actually be stored
        cleaned_data = super().clean()
        credentials = SftpCredentialSatellite(
            auth_method=cleaned_data.get("auth_method"),
            password=cleaned_data.get("password"),
            private_key=cleaned_data.get("private_key"),
        )
        try:
            credentials.clean()
        except ValidationError as error:
            self.add_error(None, error)
        return cleaned_data

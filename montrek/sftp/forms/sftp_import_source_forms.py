from django import forms

from baseclasses.forms import MontrekCreateForm
from file_upload.unattended_uploads import unattended_upload_choices
from sftp.repositories.sftp_connection_repositories import SftpConnectionRepository


class SftpImportSourceCreateForm(MontrekCreateForm):
    class Meta:
        # Written by the polls, not by people
        exclude = (
            "comment",
            "status_changed_at",
            "last_poll_status",
            "last_poll_message",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        connections = SftpConnectionRepository().receive()
        self.add_link_choice_field(
            display_field="host",
            link_name="link_sftp_import_source_sftp_connection",
            queryset=connections,
            required=True,
        )
        # Matched by hub rather than by host: two connections may share a host
        connection_hub_id = self.initial.get("sftp_connection_hub_id")
        if connection_hub_id:
            self.fields["link_sftp_import_source_sftp_connection"].initial = (
                connections.filter(hub_id=connection_hub_id).first()
            )
        # Upload managers opt in with allow_unattended_upload, so the choices
        # cannot be declared on the model
        self.fields["upload_type"] = forms.ChoiceField(
            choices=unattended_upload_choices(),
            help_text="The upload pipeline new files are handed to.",
            widget=forms.Select(attrs={"class": "form-select"}),
        )
        self.fields["upload_type"].widget.attrs["id"] = "id_upload_type"

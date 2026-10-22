from django import forms

from baseclasses.forms import MontrekCreateForm
from mailing.modules.mail_attachments import MailAttachments


class MailingSendForm(MontrekCreateForm):
    class Meta:
        exclude = ("comment", "mail_state", "hub_entity_id", "mail_comment")

    def clean_mail_attachments(self) -> str:
        # Typed in by the sender, so limited to stored files: a local path
        # would mail any file the app can read.
        attachments = MailAttachments(self.cleaned_data["mail_attachments"] or "")
        try:
            return attachments.to_storage_names()
        except ValueError as error:
            raise forms.ValidationError(str(error)) from error

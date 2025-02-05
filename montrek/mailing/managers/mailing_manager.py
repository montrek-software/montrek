import os
from smtplib import SMTPException

from baseclasses.dataclasses.montrek_message import (
    MontrekMessageError,
    MontrekMessageInfo,
)
from baseclasses.managers.montrek_manager import MontrekManager
from baseclasses.utils import get_content_type
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from mailing.repositories.mailing_repository import MailingRepository


class MailingManager(MontrekManager):
    repository_class = MailingRepository

    @property
    def template_path(self):
        return settings.EMAIL_TEMPLATE

    def send_montrek_mail(
        self,
        recipients: str,
        subject: str,
        message: str,
        additional_parms: dict = {},
        attachments: str = "",
        bcc: str = "",
    ):
        recipient_list = recipients.replace(" ", "").split(",")
        bcc_list = bcc.replace(" ", "").split(",")
        mail_params: dict = {
            "mail_subject": subject,
            "mail_recipients": recipients,
            "mail_message": message,
            "mail_state": "Pending",
            "mail_attachments": attachments,
            "mail_bcc": bcc,
        }
        mail_hub = self.repository.std_create_object(mail_params)
        body = self.get_mail_body(message, additional_parms)
        attachments_list = self.get_attachments(attachments)
        try:
            email = EmailMessage(
                subject=subject,
                body=body,
                to=recipient_list,
                attachments=attachments_list,
                bcc=bcc_list,
            )
            email.content_subtype = "html"
            email.send()
            mail_success_params = {
                "mail_state": "Sent",
                "mail_comment": "Successfully send",
                "hub_entity_id": mail_hub.id,
            }
            self.repository.std_create_object(mail_success_params)
            self.messages.append(
                MontrekMessageInfo(message=f"Mail successfully sent to {recipients}")
            )
        except SMTPException as e:
            mail_fail_params = {
                "mail_state": "Failed",
                "mail_comment": str(e),
                "hub_entity_id": mail_hub.id,
            }
            self.repository.std_create_object(mail_fail_params)
            self.messages.append(
                MontrekMessageError(message=f"Mail failed to send to {recipients}")
            )

    def send_montrek_mail_to_user(
        self,
        subject: str,
        message: str,
        additional_parms: dict = {},
        attachments: str = "",
    ) -> None:
        user_id = self.session_data["user_id"]
        user = get_user_model().objects.get(pk=user_id)
        self.send_montrek_mail(
            user.email, subject, message, additional_parms, attachments=attachments
        )

    def get_mail_body(
        self,
        message: str,
        additional_parms: dict,
    ):
        return render_to_string(
            self.template_path, self.get_context_data(message, additional_parms)
        )

    def get_context_data(self, message: str, additional_parms: dict):
        return {"message": message, **additional_parms}

    def get_attachments(self, attachments: str):
        if attachments == "":
            return []
        attachment_list = attachments.replace(" ", "").split(",")
        output_list = []
        for attachment in attachment_list:
            output_list.append(self.get_attachment(attachment))
        return output_list

    def get_attachment(self, attachment):
        file_name = os.path.basename(attachment)
        file_content_type = get_content_type(attachment)
        file_content = open(attachment, "rb").read()
        return (file_name, file_content, file_content_type)

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from baseclasses.managers.montrek_manager import MontrekManager
from mailing.repositories.mailing_repository import MailingRepository
from baseclasses.dataclasses.montrek_message import (
    MontrekMessageInfo,
    MontrekMessageError,
)
from smtplib import SMTPException


class MailingManager(MontrekManager):
    repository_class = MailingRepository
    template_path = settings.EMAIL_TEMPLATE

    def __init__(self, recipients: str, subject: str, message: str, **kwargs):
        self.recipients = recipients
        self.subject = subject
        self.message = message
        self.context = self.get_context(message, kwargs)

    def send_montrek_mail(self):
        recipient_list = self.recipients.replace(" ", "").split(",")
        mail_params: dict = {
            "mail_subject": self.subject,
            "mail_recipients": self.recipients,
            "mail_message": self.message,
            "mail_state": "Pending",
        }
        mail_hub = self.repository.std_create_object(mail_params)
        body = self.get_mail_body()
        try:
            email = EmailMessage(
                self.subject,
                body,
                settings.EMAIL_BACKEND,
                recipient_list,
            )
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

    def get_context(self, message, kwargs):
        return kwargs.update(message=message)

    def get_mail_body(self):
        return render_to_string(self.template_path, self.context)

from django.conf import settings
from django.core.mail import send_mail
from baseclasses.managers.montrek_manager import MontrekManager
from mailing.repositories.mailing_repository import MailingRepository
from baseclasses.dataclasses.montrek_message import (
    MontrekMessageInfo,
    MontrekMessageError,
)
from smtplib import SMTPException


class MailingManager(MontrekManager):
    repository_class = MailingRepository

    def send_montrek_mail(self, recipients: str, subject: str, message: str):
        recipient_list = recipients.replace(" ", "").split(",")
        mail_params: dict = {
            "mail_subject": subject,
            "mail_recipients": recipients,
            "mail_message": message,
            "mail_state": "Pending",
        }
        mail_hub = self.repository.std_create_object(mail_params)
        try:
            send_mail(
                subject=subject,
                message=message,
                recipient_list=recipient_list,
                from_email=settings.EMAIL_BACKEND,
            )
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

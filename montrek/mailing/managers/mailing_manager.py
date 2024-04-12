from django.core.mail import send_mail
from django.conf import settings
from baseclasses.managers.montrek_manager import MontrekManager
from mailing.repositories.mailing_repository import MailingRepository


class MailingManager(MontrekManager):
    repository_class = MailingRepository

    def send_mail(self, recipients: str, subject: str, message: str):
        recipient_list = recipients.replace(" ", "").split(",")
        mail_params: dict = {
            "mail_subject": subject,
            "mail_recipients": recipients,
            "mail_message": message,
        }
        mail_hub = self.repository.std_create_object(mail_params)
        mail = send_mail(
            subject=subject,
            message=message,
            recipient_list=recipient_list,
            from_email=settings.EMAIL_BACKEND,
        )
        if mail == 1:
            mail_success_params = {
                "mail_state": "Sent",
                "comment": "Successfully send",
                "hub_entity_id": mail_hub.id,
            }
            self.repository.std_create_object(mail_success_params)

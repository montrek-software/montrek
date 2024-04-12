from django.core.mail import send_mail
from django.conf import settings
from baseclasses.managers.montrek_manager import MontrekManager
from mailing.repositories.mailing_repository import MailingRepository


class MailingManager(MontrekManager):
    repository_class = MailingRepository

    def send_mail(self, recipients: str, subject: str, message: str):
        recipient_list = recipients.replace(" ", "").split(",")
        mail = send_mail(
            subject=subject,
            message=message,
            recipient_list=recipient_list,
            from_email=settings.EMAIL_BACKEND,
        )

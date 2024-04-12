from django.test import TestCase
from django.core import mail
from mailing.managers.mailing_manager import MailingManager
from mailing.repositories.mailing_repository import MailingRepository
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class TestMailingManager(TestCase):
    def setUp(self):
        self.recipients = "a@b.de, c@e.f"
        self.subject = "Test"
        self.message = "This is a test"
        self.user = MontrekUserFactory()

    def test_send_mail(self):
        mailing_manager = MailingManager({"user_id": self.user.id})
        mailing_manager.send_mail(
            recipients=self.recipients,
            subject=self.subject,
            message=self.message,
        )
        sent_emails = mail.outbox[0]
        self.assertEqual(sent_emails.subject, self.subject)
        self.assertEqual(sent_emails.body, self.message)
        self.assertEqual(sent_emails.to, ["a@b.de", "c@e.f"])
        mail_object = MailingRepository({}).std_queryset().first()
        self.assertEqual(mail_object.mail_subject, self.subject)
        self.assertEqual(mail_object.mail_recipients, self.recipients)
        self.assertEqual(mail_object.mail_message, self.message)
        self.assertEqual(mail_object.mail_state, "Sent")

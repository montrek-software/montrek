from django.test import TestCase
from django.core import mail
from mailing.managers.mailing_manager import MailingManager


class TestMailingManager(TestCase):
    def test_send_mail(self):
        mailing_manager = MailingManager()
        mailing_manager.send_mail(
            recipients="a@b.de, c@e.f",
            subject="Test",
            message="This is a test",
        )
        sent_emails = mail.outbox[0]
        self.assertEqual(sent_emails.subject, "Test")

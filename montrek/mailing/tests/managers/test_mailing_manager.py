from unittest import mock
from django.test import TestCase
from django.core import mail
from smtplib import SMTPException
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
        mailing_manager.send_montrek_mail(
            recipients=self.recipients,
            subject=self.subject,
            message=self.message,
        )
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, self.subject)
        self.assertEqual(sent_email.to, ["a@b.de", "c@e.f"])
        self.assertTrue(sent_email.body.startswith("<html>"))
        self.assertTrue(sent_email.body.endswith("</html>\n"))
        self.assertTrue(self.message in sent_email.body)
        mail_object = MailingRepository({}).std_queryset().first()
        self.assertEqual(mail_object.mail_subject, self.subject)
        self.assertEqual(mail_object.mail_recipients, self.recipients)
        self.assertEqual(mail_object.mail_message, self.message)
        self.assertEqual(mail_object.mail_state, "Sent")
        self.assertEqual(mail_object.mail_comment, "Successfully send")

    @mock.patch(
        "mailing.managers.mailing_manager.EmailMessage.send", side_effect=SMTPException
    )
    def test_send_mail_fail(self, mock_send_mail):
        mailing_manager = MailingManager({"user_id": self.user.id})
        mailing_manager.send_montrek_mail(
            recipients="",
            subject=self.subject,
            message=self.message,
        )
        mail_object = MailingRepository({}).std_queryset().first()
        self.assertEqual(mail_object.mail_state, "Failed")
        self.assertNotEqual(mail_object.mail_comment, "Successfully send")

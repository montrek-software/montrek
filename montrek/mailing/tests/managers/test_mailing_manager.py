import os
from unittest import mock
from django.core.files.uploadedfile import SimpleUploadedFile, tempfile
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
        self.assertTrue(sent_email.body.startswith('<!doctype html>\n<html lang="en">'))
        self.assertTrue(sent_email.body.endswith("</html>\n"))
        self.assertTrue(self.message in sent_email.body)
        mail_object = MailingRepository({}).receive().first()
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
        mail_object = MailingRepository({}).receive().first()
        self.assertEqual(mail_object.mail_state, "Failed")
        self.assertNotEqual(mail_object.mail_comment, "Successfully send")

    def test_send_montrek_mail_to_user(self):
        mailing_manager = MailingManager({"user_id": self.user.id})
        mailing_manager.send_montrek_mail_to_user(
            subject=self.subject,
            message=self.message,
        )
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, self.subject)
        self.assertEqual(sent_email.to, [self.user.email])
        self.assertTrue(sent_email.body.startswith('<!doctype html>\n<html lang="en">'))
        self.assertTrue(sent_email.body.endswith("</html>\n"))
        self.assertTrue(self.message in sent_email.body)
        mail_object = MailingRepository({}).receive().first()
        self.assertEqual(mail_object.mail_subject, self.subject)
        self.assertEqual(mail_object.mail_recipients, self.user.email)
        self.assertEqual(mail_object.mail_message, self.message)
        self.assertEqual(mail_object.mail_state, "Sent")
        self.assertEqual(mail_object.mail_comment, "Successfully send")

    def test_send_mail_with_attachment(self):
        mailing_manager = MailingManager({"user_id": self.user.id})
        with tempfile.NamedTemporaryFile() as test_file:
            test_file.write(b"test")
            test_file.seek(0)
            mailing_manager.send_montrek_mail(
                recipients=self.recipients,
                subject=self.subject,
                message=self.message,
                attachments=test_file.name,
            )
            sent_email = mail.outbox[0]
            self.assertEqual(
                sent_email.attachments,
                [
                    (
                        os.path.basename(test_file.name),
                        b"test",
                        "application/octet-stream",
                    )
                ],
            )

    def test_send_mail_to_user_with_attachment(self):
        mailing_manager = MailingManager({"user_id": self.user.id})
        with tempfile.NamedTemporaryFile() as test_file:
            test_file.write(b"test")
            test_file.seek(0)
            mailing_manager.send_montrek_mail_to_user(
                subject=self.subject,
                message=self.message,
                attachments=test_file.name,
            )
            sent_email = mail.outbox[0]
            self.assertEqual(
                sent_email.attachments,
                [
                    (
                        os.path.basename(test_file.name),
                        b"test",
                        "application/octet-stream",
                    )
                ],
            )

    def test_send_mail_bcc(self):
        mailing_manager = MailingManager({"user_id": self.user.id})
        mailing_manager.send_montrek_mail(
            recipients=self.recipients,
            subject=self.subject,
            message=self.message,
            bcc="test@abc.de,rest@def.de",
        )
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.bcc, ["test@abc.de", "rest@def.de"])
        mail_object = MailingRepository({}).receive().first()
        self.assertEqual(mail_object.mail_bcc, "test@abc.de,rest@def.de")

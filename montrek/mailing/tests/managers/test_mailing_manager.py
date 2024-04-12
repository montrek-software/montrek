from django.test import TestCase
from mailing.managers.mailing_manager import MailingManager


class TestMailingManager(TestCase):
    def test_send_mail(self):
        mailing_manager = MailingManager()
        breakpoint()
        mailing_manager.send_mail(
            subject="Test",
            message="This is a test",
        )

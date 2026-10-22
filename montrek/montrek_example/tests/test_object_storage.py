"""File flows on a default storage without local paths, as an object storage.

The view tests are rerun under it, so they fail if a file is read or written
past the storage API.
"""

from django.core import mail
from django.core.files.storage import default_storage
from django.test import TestCase
from django.urls import reverse
from mailing.repositories.mailing_repository import MailingRepository
from montrek_example.tests import test_views
from testing.decorators.object_storage import object_storage
from user.tests.factories.montrek_user_factories import MontrekUserFactory


@object_storage
class TestA1UploadFileViewOnObjectStorage(
    test_views.TestMontrekExampleA1UploadFileView
):
    pass


@object_storage
class TestA1DownloadViewOnObjectStorage(test_views.TestMontrekA1RepositoryDownloadView):
    pass


@object_storage
class TestA1DownloadLogViewOnObjectStorage(
    test_views.TestMontrekA1RepositoryDownloadLogView
):
    pass


@object_storage
class TestHubAFileExportTriggerViewOnObjectStorage(
    test_views.TestHubAFileExportTriggerView
):
    pass


@object_storage
class TestHubAFileExportDownloadViewOnObjectStorage(
    test_views.TestHubAFileExportDownloadView
):
    pass


@object_storage
class TestReportMailOnObjectStorage(TestCase):
    def setUp(self):
        self.client.force_login(MontrekUserFactory(is_superuser=True))

    def test_report_pdf_is_attached_from_the_storage(self):
        response = self.client.get(
            reverse("montrek_example_report"), {"send_mail": "true"}
        )
        draft = MailingRepository({}).receive().last()
        self.assertTrue(draft.mail_attachments.startswith("latex/"))
        self.assertTrue(default_storage.exists(draft.mail_attachments))

        self.client.post(
            response.url,
            {
                "mail_recipients": draft.mail_recipients,
                "mail_subject": draft.mail_subject,
                "mail_message": draft.mail_message,
                "mail_attachments": draft.mail_attachments,
            },
        )

        [sent] = mail.outbox
        [(file_name, content, content_type)] = sent.attachments
        self.assertTrue(file_name.endswith(".pdf"))
        self.assertTrue(content.startswith(b"%PDF"))
        self.assertEqual(content_type, "application/pdf")

import tempfile
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase
from mailing.modules.mail_attachments import MailAttachments
from testing.decorators.object_storage import object_storage


@object_storage
class TestMailAttachments(TestCase):
    def test_reads_stored_files_by_name(self):
        name = default_storage.save("latex/abc/Monthly report.pdf", ContentFile(b"pdf"))
        self.assertEqual(
            MailAttachments(f" {name} ,").to_email_attachments(),
            [("Monthly report.pdf", b"pdf", "application/pdf")],
        )

    def test_reads_local_files_by_absolute_path(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as file:
            file.write(b"text")
            file.flush()
            [(file_name, content, _)] = MailAttachments(
                file.name
            ).to_email_attachments()
        self.assertEqual((file_name, content), (Path(file.name).name, b"text"))

    def test_no_attachments(self):
        self.assertEqual(MailAttachments("").to_email_attachments(), [])

    def test_storage_names_are_kept(self):
        first = default_storage.save("latex/a/first.pdf", ContentFile(b"1"))
        second = default_storage.save("latex/b/second.pdf", ContentFile(b"2"))
        self.assertEqual(
            MailAttachments(f"{first}, {second}").to_storage_names(),
            f"{first},{second}",
        )

    def test_paths_under_media_root_become_storage_names(self):
        name = default_storage.save("latex/a/report.pdf", ContentFile(b"1"))
        path = Path(settings.MEDIA_ROOT) / name
        self.assertEqual(MailAttachments(str(path)).to_storage_names(), name)

    def test_files_outside_the_storage_are_refused(self):
        default_storage.save("latex/a/report.pdf", ContentFile(b"1"))
        for entry in (
            "/etc/passwd",
            f"{settings.MEDIA_ROOT}/../outside.txt",
            "latex/a/../../../outside.txt",
            "latex/a/missing.pdf",
        ):
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                MailAttachments(entry).to_storage_names()


class TestMailAttachmentsOnFilesystem(TestCase):
    def test_directories_are_refused(self):
        name = default_storage.save("latex/a/report.pdf", ContentFile(b"1"))
        media_root_directory = str(Path(settings.MEDIA_ROOT) / "latex")
        for entry in (
            ".",
            "latex",
            "latex/a",
            media_root_directory,
            str(Path(name).parent) + "/",
        ):
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                MailAttachments(entry).to_storage_names()

    def test_stored_files_are_accepted(self):
        name = default_storage.save("latex/a/report.pdf", ContentFile(b"1"))
        self.assertEqual(MailAttachments(name).to_storage_names(), name)

from django.test import SimpleTestCase

from file_upload.tests.mocks import (
    MockFileUploadManager,
    MockUnattendedFileUploadManager,
)
from file_upload.unattended_uploads import (
    UnknownUnattendedUploadError,
    accepts_file,
    get_unattended_upload_manager_class,
    unattended_upload_choices,
    unattended_upload_key,
)

UNATTENDED_KEY = "file_upload.tests.mocks.MockUnattendedFileUploadManager"
A1_KEY = "montrek_example.managers.a1_file_upload_manager.A1FileUploadManager"


class TestUnattendedUploadRegistry(SimpleTestCase):
    def test_key_is_dotted_path(self):
        self.assertEqual(
            unattended_upload_key(MockUnattendedFileUploadManager), UNATTENDED_KEY
        )

    def test_opted_in_manager_resolves(self):
        self.assertIs(
            get_unattended_upload_manager_class(UNATTENDED_KEY),
            MockUnattendedFileUploadManager,
        )

    def test_manager_without_opt_in_is_refused(self):
        key = unattended_upload_key(MockFileUploadManager)
        with self.assertRaises(UnknownUnattendedUploadError):
            get_unattended_upload_manager_class(key)

    def test_unknown_key_is_refused(self):
        for key in (
            "file_upload.tests.mocks.Missing",
            "not_an_app.module.Manager",
            "os.system",
            "nonsense",
        ):
            with (
                self.subTest(key=key),
                self.assertRaisesMessage(UnknownUnattendedUploadError, repr(key)),
            ):
                get_unattended_upload_manager_class(key)

    def test_choices_list_opted_in_managers_only(self):
        choices = dict(unattended_upload_choices())
        self.assertEqual(choices[A1_KEY], "Example A1 upload")
        self.assertEqual(choices[UNATTENDED_KEY], "Mock Unattended File Upload Manager")
        self.assertNotIn(unattended_upload_key(MockFileUploadManager), choices)


class TestAcceptsFile(SimpleTestCase):
    def test_accepts_extensions_case_insensitively(self):
        manager_class = MockUnattendedFileUploadManager
        self.assertTrue(accepts_file(manager_class, "data.csv"))
        self.assertTrue(accepts_file(manager_class, "data.CSV"))
        self.assertTrue(accepts_file(manager_class, "notes.txt"))
        self.assertFalse(accepts_file(manager_class, "data.pdf"))
        self.assertFalse(accepts_file(manager_class, "csv"))

    def test_applies_file_pattern(self):
        manager_class = MockUnattendedFileUploadManager
        self.assertTrue(accepts_file(manager_class, "positions_1.csv", "positions_*"))
        self.assertFalse(accepts_file(manager_class, "trades_1.csv", "positions_*"))
        self.assertTrue(accepts_file(manager_class, "trades_1.csv", ""))

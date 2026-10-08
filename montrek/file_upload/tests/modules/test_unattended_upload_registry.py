from django.test import SimpleTestCase

from file_upload.tests.mocks import (
    MockFileUploadManager,
    MockUnattendedFileUploadManager,
)
from file_upload.modules.unattended_upload_registry import (
    UnattendedUploadRegistry,
    UnknownUnattendedUploadError,
)

UNATTENDED_KEY = "file_upload.tests.mocks.MockUnattendedFileUploadManager"
A1_KEY = "montrek_example.managers.a1_file_upload_manager.A1FileUploadManager"


class TestUnattendedUploadRegistry(SimpleTestCase):
    def test_key_is_dotted_path(self):
        self.assertEqual(
            UnattendedUploadRegistry.key(MockUnattendedFileUploadManager),
            UNATTENDED_KEY,
        )

    def test_opted_in_manager_resolves(self):
        self.assertIs(
            UnattendedUploadRegistry.get_manager_class(UNATTENDED_KEY),
            MockUnattendedFileUploadManager,
        )

    def test_manager_without_opt_in_is_refused(self):
        key = UnattendedUploadRegistry.key(MockFileUploadManager)
        with self.assertRaises(UnknownUnattendedUploadError):
            UnattendedUploadRegistry.get_manager_class(key)

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
                UnattendedUploadRegistry.get_manager_class(key)

    def test_choices_list_opted_in_managers_only(self):
        choices = dict(UnattendedUploadRegistry.choices())
        self.assertEqual(choices[A1_KEY], "Example A1 upload")
        self.assertEqual(choices[UNATTENDED_KEY], "Mock Unattended File Upload Manager")
        self.assertNotIn(UnattendedUploadRegistry.key(MockFileUploadManager), choices)


class TestAcceptsFile(SimpleTestCase):
    def test_accepts_extensions_case_insensitively(self):
        manager_class = MockUnattendedFileUploadManager
        self.assertTrue(
            UnattendedUploadRegistry.accepts_file(manager_class, "data.csv")
        )
        self.assertTrue(
            UnattendedUploadRegistry.accepts_file(manager_class, "data.CSV")
        )
        self.assertTrue(
            UnattendedUploadRegistry.accepts_file(manager_class, "notes.txt")
        )
        self.assertFalse(
            UnattendedUploadRegistry.accepts_file(manager_class, "data.pdf")
        )
        self.assertFalse(UnattendedUploadRegistry.accepts_file(manager_class, "csv"))

    def test_applies_file_pattern(self):
        manager_class = MockUnattendedFileUploadManager
        self.assertTrue(
            UnattendedUploadRegistry.accepts_file(
                manager_class, "positions_1.csv", "positions_*"
            )
        )
        self.assertFalse(
            UnattendedUploadRegistry.accepts_file(
                manager_class, "trades_1.csv", "positions_*"
            )
        )
        self.assertTrue(
            UnattendedUploadRegistry.accepts_file(manager_class, "trades_1.csv", "")
        )

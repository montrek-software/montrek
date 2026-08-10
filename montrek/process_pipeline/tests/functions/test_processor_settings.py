from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import SimpleTestCase, TestCase

from process_pipeline.functions.processor_settings import (
    ProcessorSettingsMixin,
    resolve_settings,
)

SETTINGS_DIR = Path(__file__).resolve().parent / "settings"
UPLOADED_TOML = b'[report]\ntitle = "Uploaded"\n'


class PackagedSettingsFunctions(ProcessorSettingsMixin):
    label: ClassVar[str] = "Packaged"

    @classmethod
    def get_settings_path(cls) -> Path:
        return SETTINGS_DIR


class OptionalSettingsFunctions(PackagedSettingsFunctions):
    require_packaged_settings: ClassVar[bool] = False

    @classmethod
    def get_settings_path(cls) -> Path:
        return SETTINGS_DIR / "does_not_exist"


class NoSettingsFunctions:
    has_settings = False


class TestSettingsDiscovery(SimpleTestCase):
    def test_finds_the_packaged_settings(self):
        names = [s.name for s in PackagedSettingsFunctions.get_available_settings()]
        self.assertEqual(names, ["example"])

    def test_does_not_create_a_missing_settings_folder(self):
        """Discovery must stay read-only to work on a read-only deployment."""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            OptionalSettingsFunctions.get_available_settings()
        mock_mkdir.assert_not_called()
        self.assertFalse(OptionalSettingsFunctions.get_settings_path().exists())

    def test_missing_folder_yields_no_choices_when_not_required(self):
        self.assertEqual(OptionalSettingsFunctions.get_settings_choices(), [])

    def test_missing_folder_raises_when_packaged_settings_are_required(self):
        class RequiredSettingsFunctions(PackagedSettingsFunctions):
            @classmethod
            def get_settings_path(cls) -> Path:
                return SETTINGS_DIR / "does_not_exist"

        with self.assertRaises(FileNotFoundError):
            RequiredSettingsFunctions.get_available_settings()


class TestResolveSettings(SimpleTestCase):
    def test_loads_the_named_packaged_settings(self):
        settings = resolve_settings(PackagedSettingsFunctions, settings_name="example")
        self.assertEqual(settings["report"]["title"], "Packaged")

    def test_returns_empty_when_the_class_has_no_settings(self):
        self.assertEqual(resolve_settings(NoSettingsFunctions), {})

    def test_requires_a_name_when_the_class_has_settings(self):
        with self.assertRaises(KeyError):
            resolve_settings(PackagedSettingsFunctions)


class TestResolveUploadedSettings(TestCase):
    """The upload travels as a storage name so another host can still read it."""

    def setUp(self):
        self.storage_name = default_storage.save(
            "test_settings/uploaded.toml", ContentFile(UPLOADED_TOML)
        )
        self.addCleanup(default_storage.delete, self.storage_name)

    def test_reads_the_upload_through_the_storage_backend(self):
        settings = resolve_settings(
            PackagedSettingsFunctions, settings_file_name=self.storage_name
        )
        self.assertEqual(settings["report"]["title"], "Uploaded")

    def test_upload_wins_over_the_selected_settings(self):
        settings = resolve_settings(
            PackagedSettingsFunctions,
            settings_name="example",
            settings_file_name=self.storage_name,
        )
        self.assertEqual(settings["report"]["title"], "Uploaded")

    def test_a_missing_upload_raises(self):
        with self.assertRaises(FileNotFoundError):
            resolve_settings(
                PackagedSettingsFunctions,
                settings_file_name="test_settings/not_there.toml",
            )

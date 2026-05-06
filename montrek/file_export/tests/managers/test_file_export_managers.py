from django.test import TestCase

from file_export.tests.mocks import (
    MockFileExportManager,
    MockFileExportManagerFailPostCheck,
    MockFileExportManagerFailPreCheck,
    MockFileExportManagerFailProcess,
    MockFileExportManagerNoFile,
    MockFileExportRegistryRepository,
)
from testing.decorators import add_logged_in_user


class TestFileExportManager(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.manager = MockFileExportManager({"user_id": self.user.id})

    def test_init_registry(self):
        self.manager.create_registry()
        self.manager._load_registry()
        registry = self.manager.get_registry()
        self.assertEqual(registry.export_status, "pending")
        self.assertEqual(registry.export_message, "Export is pending")

    def test_trigger_export__success(self):
        self.manager.trigger_export()
        registry = self.manager.get_registry()
        self.assertEqual(registry.export_status, "processed")
        self.assertEqual(registry.export_message, "Export successful")

    def test_trigger_export__file_attached(self):
        self.manager.trigger_export()
        registry = self.manager.get_registry()
        self.assertTrue(bool(registry.export_file))

    def test_trigger_export__pre_check_fails(self):
        manager = MockFileExportManagerFailPreCheck({"user_id": self.user.id})
        manager.trigger_export()
        registry = manager.get_registry()
        self.assertEqual(registry.export_status, "failed")
        self.assertEqual(registry.export_message, "Pre Check Failed")

    def test_trigger_export__process_fails(self):
        manager = MockFileExportManagerFailProcess({"user_id": self.user.id})
        manager.trigger_export()
        registry = manager.get_registry()
        self.assertEqual(registry.export_status, "failed")
        self.assertEqual(registry.export_message, "Process Failed")

    def test_trigger_export__post_check_fails(self):
        manager = MockFileExportManagerFailPostCheck({"user_id": self.user.id})
        manager.trigger_export()
        registry = manager.get_registry()
        self.assertEqual(registry.export_status, "failed")
        self.assertEqual(registry.export_message, "Post Check Failed")

    def test_trigger_export__no_file_does_not_crash(self):
        manager = MockFileExportManagerNoFile({"user_id": self.user.id})
        result = manager.trigger_export()
        self.assertTrue(result)
        registry = manager.get_registry()
        self.assertEqual(registry.export_status, "processed")
        self.assertFalse(bool(registry.export_file))

    def test_registry_count_after_export(self):
        self.manager.trigger_export()
        registry_query = MockFileExportRegistryRepository().receive()
        self.assertEqual(registry_query.count(), 1)

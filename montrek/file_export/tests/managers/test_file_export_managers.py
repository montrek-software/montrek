import unittest

from file_export.tests.mocks import (
    MockFileExportManager,
    MockFileExportManagerFailPostCheck,
    MockFileExportManagerFailPreCheck,
    MockFileExportManagerFailProcess,
    MockFileExportManagerNoFile,
)

SESSION = {"user_id": 1}


class TestFileExportManager(unittest.TestCase):
    def setUp(self):
        self.manager = MockFileExportManager(SESSION)

    def _last_update(self, manager=None):
        m = manager or self.manager
        return m._registry_updates[-1]

    def _file_update(self, manager=None):
        m = manager or self.manager
        return next((u for u in m._registry_updates if "export_file" in u), None)

    # ---- registry initialisation ----

    def test_create_registry_sets_session_key(self):
        self.manager.create_registry()
        self.assertEqual(
            self.manager.session_data[self.manager.registry_session_key], 1
        )

    # ---- happy path ----

    def test_trigger_export__returns_true(self):
        self.assertTrue(self.manager.trigger_export())

    def test_trigger_export__final_status_processed(self):
        self.manager.trigger_export()
        self.assertEqual(self._last_update()["export_status"], "processed")

    def test_trigger_export__final_message(self):
        self.manager.trigger_export()
        self.assertEqual(self._last_update()["export_message"], "Export successful")

    def test_trigger_export__file_attached_to_registry(self):
        self.manager.trigger_export()
        file_update = self._file_update()
        self.assertIsNotNone(
            file_update, "expected an _update_registry call with export_file"
        )
        self.assertIsNotNone(file_update["export_file"])

    def test_trigger_export__in_progress_set_before_steps(self):
        self.manager.trigger_export()
        first = self.manager._registry_updates[0]
        self.assertEqual(first["export_status"], "in_progress")

    # ---- failure paths ----

    def test_pre_check_fails__status_failed(self):
        m = MockFileExportManagerFailPreCheck(SESSION)
        m.trigger_export()
        self.assertEqual(self._last_update(m)["export_status"], "failed")
        self.assertEqual(self._last_update(m)["export_message"], "Pre Check Failed")

    def test_process_fails__status_failed(self):
        m = MockFileExportManagerFailProcess(SESSION)
        m.trigger_export()
        self.assertEqual(self._last_update(m)["export_status"], "failed")
        self.assertEqual(self._last_update(m)["export_message"], "Process Failed")

    def test_post_check_fails__status_failed(self):
        m = MockFileExportManagerFailPostCheck(SESSION)
        m.trigger_export()
        self.assertEqual(self._last_update(m)["export_status"], "failed")
        self.assertEqual(self._last_update(m)["export_message"], "Post Check Failed")

    # ---- no-file path ----

    def test_no_file__returns_true(self):
        m = MockFileExportManagerNoFile(SESSION)
        self.assertTrue(m.trigger_export())

    def test_no_file__no_export_file_update(self):
        m = MockFileExportManagerNoFile(SESSION)
        m.trigger_export()
        self.assertIsNone(self._file_update(m))

    def test_no_file__status_processed(self):
        m = MockFileExportManagerNoFile(SESSION)
        m.trigger_export()
        self.assertEqual(self._last_update(m)["export_status"], "processed")

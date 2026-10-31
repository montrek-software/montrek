from django.test import TestCase

from file_upload.managers.file_upload_registry_manager import (
    FileUploadRegistryManager,
)
from process_pipeline.dataclasses.registry_table_elements import (
    RegistryStatusTableElement,
)
from reporting.dataclasses.table_elements import LabelTableElement


class StillFileUploadRegistryManager(FileUploadRegistryManager):
    live_status = False


class TestFileUploadRegistryManagerLiveStatus(TestCase):
    def test_status_is_live_by_default(self):
        manager = FileUploadRegistryManager({})
        manager.live_rows_path = "/file_upload/"
        element = manager.status_element
        self.assertIsInstance(element, RegistryStatusTableElement)
        self.assertEqual(element.rows_path, "/file_upload/")
        self.assertEqual(element.active_values, ("pending", "in_progress"))
        self.assertEqual(element.message_attr, "upload_message")
        self.assertIsNone(element.previous_value)

    def test_status_outside_a_list_view_does_not_poll(self):
        element = FileUploadRegistryManager({}).status_element
        self.assertEqual(element.rows_path, "")

    def test_live_status_can_be_switched_off(self):
        element = StillFileUploadRegistryManager({}).status_element
        self.assertIs(type(element), LabelTableElement)

    def test_poll_params_reach_the_elements(self):
        manager = FileUploadRegistryManager(
            {"live_shown": ["pending"], "live_shown_message": ["ab12"]}
        )
        self.assertEqual(manager.status_element.previous_value, "pending")
        self.assertEqual(manager.message_element.previous_digest, "ab12")

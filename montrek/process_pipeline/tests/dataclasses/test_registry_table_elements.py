from django.test import TestCase

from process_pipeline.dataclasses.registry_table_elements import (
    RegistryMessageTableElement,
    RegistryStatusTableElement,
)


class TestRegistryMessageTableElement(TestCase):
    def test_digest_treats_none_as_empty(self):
        self.assertEqual(
            RegistryMessageTableElement.digest(None),
            RegistryMessageTableElement.digest(""),
        )
        self.assertNotEqual(
            RegistryMessageTableElement.digest("a"),
            RegistryMessageTableElement.digest("b"),
        )

    def test_changed_message_is_marked(self):
        shown_digest = RegistryMessageTableElement.digest("Step 1 of 3")
        for message, is_changed in (
            ("Step 1 of 3", False),
            ("Step 2 of 3", True),
        ):
            with self.subTest(message=message):
                element = RegistryMessageTableElement(
                    name="Message", attr="message", previous_digest=shown_digest
                )
                display_field = element.get_display_field({"message": message})
                self.assertEqual(
                    "mt-live-cell-changed" in display_field.td_classes_str,
                    is_changed,
                )

    def test_message_outside_a_poll_is_not_marked(self):
        element = RegistryMessageTableElement(name="Message", attr="message")
        display_field = element.get_display_field({"message": "Done"})
        self.assertNotIn("mt-live-cell-changed", display_field.td_classes_str)


class TestRegistryStatusTableElement(TestCase):
    def test_poll_sends_the_shown_message_digest(self):
        element = RegistryStatusTableElement(
            name="Status", attr="status", message_attr="upload_message"
        )
        params = element.get_poll_params(
            "pending", {"id": 3, "status": "pending", "upload_message": "Queued"}
        )
        self.assertEqual(
            params,
            {
                "live_row": "3",
                "live_shown": "pending",
                "live_shown_message": RegistryMessageTableElement.digest("Queued"),
            },
        )

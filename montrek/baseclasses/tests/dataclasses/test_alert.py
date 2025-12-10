from baseclasses.dataclasses.alert import AlertEnum
from django.test import TestCase


class TestAlert(TestCase):
    def setUp(self):
        self.alert_enum = AlertEnum

    def test_get_by_description(self):
        for description, value in (("error", -2), ("warning", -1), ("ok", 0)):
            self.assertEqual(
                self.alert_enum.get_by_description(description).sort_order, value
            )

    def test_get_by_description__invalid_description(self):
        self.assertEqual(self.alert_enum.get_by_description("invalid").sort_order, -3)
        self.assertEqual(
            self.alert_enum.get_by_description("invalid").description, "unknown"
        )

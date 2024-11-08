from django.test import TestCase
from django.urls import reverse

from baseclasses.dataclasses.view_classes import (
    BackActionElement,
    ActionElement,
    SettingsActionElement,
    StandardActionElementBase,
    UploadActionElement,
    CreateActionElement,
    RegistryActionElement,
)


class TestStandardActionElementBase(TestCase):
    def test_init(self):
        url_name = "montrek_example_a_list"
        element = StandardActionElementBase(
            url_name=url_name,
        )
        self.assertTrue(isinstance(element, ActionElement))
        self.assertEqual(element.icon, "")
        self.assertEqual(element.link, reverse(url_name))
        self.assertEqual(element.action_id, "id_action_montrek_example_a_list")
        self.assertEqual(element.hover_text, "Go to Montrek Example A List")


class TestStandardActionElements(TestCase):
    def test_init(self):
        url_name = "montrek_example_a_list"

        expected_icons = (
            (BackActionElement, "arrow-left"),
            (UploadActionElement, "upload"),
            (SettingsActionElement, "cog"),
            (CreateActionElement, "plus"),
            (RegistryActionElement, "inbox"),
        )

        for element_class, expected_icon in expected_icons:
            element = element_class(url_name=url_name)
            self.assertTrue(isinstance(element, StandardActionElementBase))
            self.assertEqual(element.icon, expected_icon)

from baseclasses.dataclasses.view_classes import (
    ActionElement,
    BackActionElement,
    CreateActionElement,
    ListActionElement,
    PlayActionElement,
    RegistryActionElement,
    SettingsActionElement,
    ShowActionElement,
    StandardActionElementBase,
    UploadActionElement,
)
from django.test import TestCase
from django.urls import reverse


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
            (ListActionElement, "align-justify"),
            (PlayActionElement, "play"),
            (ShowActionElement, "eye"),
        )

        for element_class, expected_icon in expected_icons:
            element = element_class(url_name=url_name)
            self.assertTrue(isinstance(element, StandardActionElementBase))
            self.assertEqual(element.icon, expected_icon)

    def test_with_kwargs(self):
        url_name = "montrek_example_a_details"
        action_id = "id_custom_action"
        hover_text = "Custom Action"
        kwargs = {"pk": 1}
        expected_icons = (
            (BackActionElement, "arrow-left"),
            (UploadActionElement, "upload"),
            (SettingsActionElement, "cog"),
            (CreateActionElement, "plus"),
            (RegistryActionElement, "inbox"),
            (PlayActionElement, "play"),
            (ShowActionElement, "eye"),
        )
        for element_class, expected_icon in expected_icons:
            element = element_class(
                url_name=url_name,
                kwargs=kwargs,
                action_id=action_id,
                hover_text=hover_text,
            )
            self.assertTrue(isinstance(element, StandardActionElementBase))
            self.assertEqual(element.icon, expected_icon)
            self.assertEqual(element.link, reverse(url_name, kwargs=kwargs))
            self.assertEqual(element.action_id, action_id)
            self.assertEqual(element.hover_text, hover_text)

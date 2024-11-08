from django.test import TestCase
from django.urls import reverse

from baseclasses.dataclasses.view_classes import (
    BackActionElement,
    ActionElement,
    StandardActionElementBase,
)


class TestStandardActionElement(TestCase):
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


class TestBackActionElement(TestCase):
    def test_init(self):
        url_name = "montrek_example_a_list"
        element = BackActionElement(url_name=url_name)

        self.assertTrue(isinstance(element, StandardActionElementBase))
        self.assertEqual(element.icon, "arrow-left")

from django.test import TestCase

from baseclasses.dataclasses.view_classes import BackActionElement, ActionElement


class TestBackActionElement(TestCase):
    def test_init(self):
        element = BackActionElement(link="link")

        self.assertTrue(isinstance(element, ActionElement))
        self.assertEqual(element.icon, "arrow-left")
        self.assertEqual(element.link, "link")
        self.assertEqual(element.action_id, "id_back_action")
        self.assertEqual(element.hover_text, "Go Back")

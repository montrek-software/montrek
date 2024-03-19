from django.test import TestCase
from baseclasses.text import clean_column_name


class TestText(TestCase):
    def test_clean_column_name(self):
        self.assertEqual(clean_column_name("Hello World!"), "hello_world")
        self.assertEqual(clean_column_name("__foo_bar_"), "foo_bar")
        self.assertEqual(clean_column_name("%^H3ll0&world$"), "h3ll0_world")
        self.assertEqual(clean_column_name(""), "")
        self.assertEqual(clean_column_name("   "), "")

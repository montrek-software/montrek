from django.template.loader import render_to_string
from django.test import TestCase


class TestGoldThemeTemplate(TestCase):
    """The theme owns all component styling, so a rule a page depends on
    quietly disappearing from here is a regression nothing else would catch."""

    def setUp(self):
        self.css = render_to_string("partials/gold_theme.html")

    def test_accent_token_is_defined(self):
        self.assertIn("--mt-accent:", self.css)

    def test_selected_option_is_painted_in_the_accent_color(self):
        rule = self.css.split("option:checked")[1].split("}")[0]

        self.assertIn("var(--mt-accent)", rule)
        # A plain background-color loses to the system highlight in Blink.
        self.assertIn("linear-gradient", rule)

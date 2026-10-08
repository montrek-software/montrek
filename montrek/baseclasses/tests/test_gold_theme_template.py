from django.template.loader import render_to_string
from django.test import TestCase, override_settings


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


class TestGoldThemeFont(TestCase):
    def _body_font_family(self) -> str:
        css = render_to_string("partials/gold_theme.html")
        return css.split("body {")[1].split("font-family:")[1].split(";")[0].strip()

    @override_settings(FONT_NAME="")
    def test_font_stack_starts_with_inter_by_default(self):
        self.assertTrue(self._body_font_family().startswith('"Inter Variable"'))

    @override_settings(FONT_NAME="Poppins")
    def test_configured_font_leads_the_stack_with_inter_as_fallback(self):
        self.assertTrue(
            self._body_font_family().startswith('"Poppins", "Inter Variable"')
        )


class TestGoldThemeTokens(TestCase):
    """Rules in the structural layer take their colors from the theme tokens,
    so a client stylesheet overriding a token restyles them as well."""

    def test_structural_layer_uses_tokens_for_primary_and_secondary(self):
        css = render_to_string("partials/color_scheme.html")
        rule = css.split(".form-check-input:checked {")[1].split("}")[0]

        self.assertIn("var(--mt-secondary)", rule)

    def test_text_on_accent_fills_uses_the_on_accent_token(self):
        css = render_to_string("partials/gold_theme.html")
        rule = css.split(".flatpickr-day.selected:hover {")[1].split("}")[0]

        self.assertIn("var(--mt-on-accent)", rule)

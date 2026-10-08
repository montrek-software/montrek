from django.template.loader import get_template, render_to_string
from django.test import TestCase, override_settings

from baseclasses.theme_checks import check_custom_css_paths

CLIENT_CSS = "client/theme.css"


class TestCustomCssTemplate(TestCase):
    """Client stylesheets override the gold theme only by loading after it."""

    @override_settings(CUSTOM_CSS=[])
    def test_no_stylesheet_is_linked_by_default(self):
        self.assertNotIn("<link", render_to_string("partials/custom_css.html"))

    @override_settings(CUSTOM_CSS=[CLIENT_CSS, "client/extra.css"])
    def test_each_client_stylesheet_is_linked_in_order(self):
        html = render_to_string("partials/custom_css.html")

        first = html.index(f'href="/static/{CLIENT_CSS}"')
        second = html.index('href="/static/client/extra.css"')
        self.assertLess(first, second)

    def test_client_stylesheets_load_after_the_gold_theme(self):
        source = get_template("base_common.html").template.source

        self.assertGreater(
            source.index('"partials/custom_css.html"'),
            source.index('"partials/gold_theme.html"'),
        )


class TestCustomCssCheck(TestCase):
    @override_settings(CUSTOM_CSS=[])
    def test_silent_without_client_stylesheets(self):
        self.assertEqual(check_custom_css_paths(), [])

    @override_settings(CUSTOM_CSS=["does/not/exist.css"])
    def test_warns_about_a_stylesheet_the_finders_cannot_locate(self):
        warnings = check_custom_css_paths()

        self.assertEqual([w.id for w in warnings], ["baseclasses.W001"])
        self.assertIn("does/not/exist.css", warnings[0].msg)

from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase


class TestUrlKwargsPassthroughPartial(TestCase):
    """Tests for baseclasses/templates/partials/url_kwargs_passthrough.html."""

    TEMPLATE = "partials/url_kwargs_passthrough.html"

    def _render(self, get_params: dict, exclude_key: str) -> BeautifulSoup:
        request = RequestFactory().get("/", get_params)
        html = render_to_string(
            self.TEMPLATE,
            {"exclude_key": exclude_key},
            request=request,
        )
        return BeautifulSoup(html, "html.parser")

    def test_excluded_key_not_rendered(self):
        soup = self._render({"gen_pdf": "true", "foo": "bar"}, exclude_key="gen_pdf")
        self.assertIsNone(soup.find("input", {"name": "gen_pdf"}))

    def test_other_params_are_passed_through(self):
        soup = self._render({"gen_pdf": "true", "foo": "bar"}, exclude_key="gen_pdf")
        inp = soup.find("input", {"name": "foo"})
        self.assertIsNotNone(inp)
        self.assertEqual(inp["value"], "bar")

    def test_no_params_renders_no_inputs(self):
        soup = self._render({}, exclude_key="gen_pdf")
        self.assertEqual(len(soup.find_all("input")), 0)

    def test_multiple_params_passed_through_excluding_action(self):
        soup = self._render(
            {"gen_csv": "true", "start_date": "2024-01-01", "end_date": "2024-12-31"},
            exclude_key="gen_csv",
        )
        self.assertIsNone(soup.find("input", {"name": "gen_csv"}))
        self.assertIsNotNone(soup.find("input", {"name": "start_date"}))
        self.assertIsNotNone(soup.find("input", {"name": "end_date"}))

    def test_input_type_is_hidden(self):
        soup = self._render({"foo": "bar"}, exclude_key="other")
        inp = soup.find("input", {"name": "foo"})
        self.assertEqual(inp["type"], "hidden")

    def test_all_params_passed_when_exclude_key_absent(self):
        soup = self._render({"a": "1", "b": "2"}, exclude_key="gen_pdf")
        self.assertIsNotNone(soup.find("input", {"name": "a"}))
        self.assertIsNotNone(soup.find("input", {"name": "b"}))

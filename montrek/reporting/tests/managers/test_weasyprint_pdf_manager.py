import tempfile

from bs4 import BeautifulSoup
from django.test import TestCase, override_settings
from reporting.managers.weasyprint_pdf_manager import WeasyPrintPdfManager
from reporting.tests.mocks import (
    MockMontrekReportManager,
    MockMontrekTableManager,
)


class _BrokenManager:
    def to_pdf_html(self):
        raise RuntimeError("broken intentionally")


class _TitlelessManager:
    def to_pdf_html(self):
        return "<p>no title attrs</p>"


class TestWeasyPrintPdfManagerGenerate(TestCase):
    def test_generate_pdf_returns_pdf_bytes(self):
        result = WeasyPrintPdfManager(MockMontrekTableManager()).generate_pdf()
        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b"%PDF"), "Expected a PDF byte stream")

    def test_generate_pdf_returns_none_on_exception(self):
        result = WeasyPrintPdfManager(_BrokenManager()).generate_pdf()
        self.assertIsNone(result)


class TestWeasyPrintPdfManagerTitle(TestCase):
    def test_title_from_document_title(self):
        pdf_manager = WeasyPrintPdfManager(MockMontrekReportManager({}))
        self.assertEqual(pdf_manager._title, "Mock Report")

    def test_title_from_table_title_when_document_title_is_falsy(self):
        manager = MockMontrekTableManager()
        manager.document_title = ""
        pdf_manager = WeasyPrintPdfManager(manager)
        self.assertEqual(pdf_manager._title, "Mock Table")

    def test_title_falls_back_to_empty_string(self):
        pdf_manager = WeasyPrintPdfManager(_TitlelessManager())
        self.assertEqual(pdf_manager._title, "")


class TestWeasyPrintPdfManagerClientLogoSrc(TestCase):
    def test_https_url_returned_as_is(self):
        with override_settings(CLIENT_LOGO_PATH="https://example.com/logo.png"):
            self.assertEqual(
                WeasyPrintPdfManager._client_logo_src(),
                "https://example.com/logo.png",
            )

    def test_http_url_returned_as_is(self):
        with override_settings(CLIENT_LOGO_PATH="http://example.com/logo.png"):
            self.assertEqual(
                WeasyPrintPdfManager._client_logo_src(),
                "http://example.com/logo.png",
            )

    def test_valid_local_path_prefixed_with_file_scheme(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as f, override_settings(
            CLIENT_LOGO_PATH=f.name
        ):
            result = WeasyPrintPdfManager._client_logo_src()
            self.assertEqual(result, f"file://{f.name}")

    def test_nonexistent_local_path_returns_empty(self):
        with override_settings(CLIENT_LOGO_PATH="/nonexistent/logo.png"):
            self.assertEqual(WeasyPrintPdfManager._client_logo_src(), "")

    def test_empty_setting_returns_empty(self):
        with override_settings(CLIENT_LOGO_PATH=""):
            self.assertEqual(WeasyPrintPdfManager._client_logo_src(), "")


class TestWeasyPrintPdfManagerRenderHtml(TestCase):
    def test_render_html_contains_title(self):
        manager = MockMontrekTableManager()
        html = WeasyPrintPdfManager(manager)._render_html()
        self.assertIn(manager.table_title, html)

    def test_render_html_contains_table(self):
        html = WeasyPrintPdfManager(MockMontrekTableManager())._render_html()
        self.assertIn("<table", html)

    def test_render_html_default_orientation_is_landscape(self):
        html = WeasyPrintPdfManager(MockMontrekTableManager())._render_html()
        self.assertIn("landscape", html)

    def test_render_html_respects_portrait_orientation(self):
        manager = MockMontrekTableManager()
        manager.pdf_orientation = "portrait"
        html = WeasyPrintPdfManager(manager)._render_html()
        self.assertIn("portrait", html)

    @override_settings(CLIENT_LOGO_PATH="https://example.com/logo.png")
    def test_render_html_includes_client_logo_url(self):
        html = WeasyPrintPdfManager(MockMontrekTableManager())._render_html()
        self.assertIn("https://example.com/logo.png", html)

    @override_settings(CLIENT_LOGO_PATH="")
    def test_render_html_omits_logo_div_when_no_logo(self):
        html = WeasyPrintPdfManager(MockMontrekTableManager())._render_html()
        soup = BeautifulSoup(html, "html.parser")
        self.assertIsNone(soup.find("div", id="page-header-logo"))

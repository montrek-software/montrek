from bs4 import BeautifulSoup
from django.test import TestCase, override_settings
from mailing.models import MailHub
from testing.decorators.add_logged_in_user import add_logged_in_user

from reporting.managers.latex_report_manager import LatexReportManager
from reporting.tests import mocks
from testing.decorators.mock_plotly_image_write import (
    mock_plotly_write_dummy_png,
)


class TestMontrekReportManager(TestCase):
    def test_init(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        self.assertEqual(manager.session_data, session_data)
        self.assertEqual(manager._report_elements, [])

    def test_no_collect_report_elements(self):
        manager = mocks.MockNoCollectReportElements(session_data={})
        self.assertRaises(NotImplementedError, manager.collect_report_elements)

    def test_append_report_element(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        report_element = mocks.MockReportElement()
        manager.append_report_element(report_element)
        self.assertEqual(manager.report_elements, [report_element])

    def test_append_report_element_list(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        report_element = mocks.MockReportElement()
        manager.append_report_element(report_element)
        manager.append_report_element([report_element, report_element])
        self.assertEqual(
            manager.report_elements,
            [
                report_element,
                report_element,
                report_element,
            ],
        )

    def test_generate_report(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        report_element = mocks.MockReportElement()
        manager.append_report_element(report_element)
        manager.append_report_element(report_element)
        self.assertEqual(manager.generate_report(), "htmllatexhtmllatex")

    def test_cleanup_report_elements(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        manager.cleanup_report_elements()
        self.assertEqual(manager.report_elements, [])

    def test_cleanup_after_to_html(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        manager.append_report_element(mocks.MockReportElement())
        manager.to_html()
        self.assertEqual(manager.report_elements, [])

    def test_cleanup_after_to_latex(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        manager.append_report_element(mocks.MockReportElement())
        manager.to_latex()
        self.assertEqual(manager.report_elements, [])

    def test_failing_report_generation(self):
        session_data = {}
        manager = mocks.MockMontrekReportManagerError(session_data=session_data)
        manager.append_report_element(mocks.MockReportElement())
        test_html = manager.to_html()[0]
        self.assertIn(
            '<div class="alert alert-danger"><strong>Error during report generation: This fails!</strong></div>',
            test_html,
        )
        self.assertIn(
            "Traceback (most recent call last):",
            test_html,
        )
        self.assertIn(
            "ValueError: This fails!",
            test_html,
        )
        self.assertEqual(manager.report_elements, [])

    @override_settings(DEBUG=False)
    def test_failing_report_generation__no_debug(self):
        session_data = {}
        manager = mocks.MockMontrekReportManagerError(session_data=session_data)
        manager.append_report_element(mocks.MockReportElement())
        html = manager.to_html()[0]
        soup = BeautifulSoup(html, "html.parser")

        alerts = soup.find_all("div", class_="alert")
        self.assertEqual(len(alerts), 2)

        # First alert: error
        error_alert = alerts[0]
        self.assertIn("alert-danger", error_alert.get("class", []))
        self.assertIn(
            "Error during report generation: This fails!",
            error_alert.get_text(strip=True),
        )

        # Second alert: non-debug message
        fallback_alert = alerts[1]
        self.assertIn(
            "Contact admin and check Debug mode",
            fallback_alert.get_text(strip=True),
        )

        # Report elements must be cleared
        self.assertEqual(manager.report_elements, [])

    def test_failing_report_generation_while_to_html(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        manager.append_report_element(mocks.MockReportElementError())
        test_html = manager.to_html()[0]
        self.assertIn(
            '<div class="alert alert-danger"><strong>Error during report generation: This fails!</strong></div>',
            test_html,
        )
        self.assertIn(
            "Traceback (most recent call last):",
            test_html,
        )
        self.assertIn(
            "ValueError: This fails!",
            test_html,
        )
        self.assertEqual(manager.report_elements, [])

    @override_settings(DEBUG=False)
    def test_failing_report_generation__no_debug_while_to_html(self):
        session_data = {}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        manager.append_report_element(mocks.MockReportElementError())
        html = manager.to_html()[0]
        soup = BeautifulSoup(html, "html.parser")

        alerts = soup.find_all("div", class_="alert")
        self.assertEqual(len(alerts), 2)

        # First alert: error message
        error_alert = alerts[0]
        self.assertIn("alert-danger", error_alert.get("class", []))
        self.assertIn(
            "Error during report generation: This fails!",
            error_alert.get_text(strip=True),
        )

        # Second alert: non-debug message
        fallback_alert = alerts[1]
        self.assertIn(
            "Contact admin and check Debug mode",
            fallback_alert.get_text(strip=True),
        )

        # Report elements must be cleared
        self.assertEqual(manager.report_elements, [])

    @add_logged_in_user
    def test_prepare_mail_redirect_to_correct_mail(self):
        MailHub().save()
        session_data = {"user_id": self.user.id}
        manager = mocks.MockMontrekReportManager(session_data=session_data)
        redirect = manager.prepare_mail("")
        self.assertEqual(redirect.status_code, 302)


class TestComprehensiveReport(TestCase):
    @mock_plotly_write_dummy_png()
    def test_generate_report_and_compile(self, mock_write_image):
        session_data = {}
        manager = mocks.MockComprehensiveReportManager(session_data=session_data)
        self.assertEqual(manager.document_title, "Mock Comprehensive Report")
        report_manager = LatexReportManager(manager)
        pdf_path = report_manager.compile_report()
        self.assertIn("document.pdf", pdf_path)
        mock_write_image.assert_called_once()

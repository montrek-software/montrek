from datetime import date

from django.test import TestCase
from freezegun import freeze_time
from reporting.forms import ReportDateReportForm
from reporting.tests.mocks import (
    MockMontrekReportForm,
    MockNoTemplateMontrekReportForm,
    MockTemplateNotFoundMontrekReportForm,
)


class TestMontrekReportForm(TestCase):
    def test_no_template(self):
        self.assertRaises(
            NotImplementedError,
            MockNoTemplateMontrekReportForm().to_html,
        )

    def test_template_not_found(self):
        self.assertRaises(
            FileNotFoundError,
            MockTemplateNotFoundMontrekReportForm().to_html,
        )

    def test_render_template(self):
        form = MockMontrekReportForm()
        test_html = form.to_html()
        self.assertEqual(
            test_html.replace(" ", ""),
            '<form method="post" class="tile">\n  <fieldset>\n  <legend>Test</legend>\n  <input type="text" name="field_1" required id="id_field_1">\n</fieldset>\n\n    <button type="submit" class="btn btn-custom">Submit</button>\n    </form>\n'.replace(
                " ", ""
            ),
        )


@freeze_time("2026-01-15")
class TestReportDateReportForm(TestCase):
    def test_initial_is_callable(self):
        """Guards against date.today() being frozen at class definition time."""
        field = ReportDateReportForm.base_fields["report_date"]
        self.assertTrue(callable(field.initial))

    def test_unbound_form_initial_is_today(self):
        """Unbound form renders today's date into the value attribute."""
        form = ReportDateReportForm()
        expected = date.today().strftime("%Y-%m-%d")
        self.assertIn(f'value="{expected}"', str(form["report_date"]))

    def test_to_html_contains_today(self):
        """to_html() output contains today's date so flatpickr can read it."""
        form = ReportDateReportForm()
        expected = date.today().strftime("%Y-%m-%d")
        self.assertIn(expected, form.to_html())

    def test_widget_format_is_iso(self):
        """Widget format must be %Y-%m-%d so flatpickr receives a parseable value."""
        widget = ReportDateReportForm.base_fields["report_date"].widget
        self.assertEqual(widget.format, "%Y-%m-%d")

    def test_valid_date_passes_validation(self):
        form = ReportDateReportForm(data={"report_date": "2026-01-15"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["report_date"], date(2026, 1, 15))

    def test_empty_date_fails_validation(self):
        form = ReportDateReportForm(data={"report_date": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("report_date", form.errors)

    def test_invalid_date_fails_validation(self):
        form = ReportDateReportForm(data={"report_date": "not-a-date"})
        self.assertFalse(form.is_valid())
        self.assertIn("report_date", form.errors)

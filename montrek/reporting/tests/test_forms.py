from django import forms
from django.test import TestCase
from reporting.forms import MontrekReportForm


class MockNoTemplateMontrekReportForm(MontrekReportForm): ...


class MockTemplateNotFoundMontrekReportForm(MontrekReportForm):
    form_template = "not_found"


class MockMontrekReportForm(MontrekReportForm):
    form_template = "test_form.html"
    field_1 = forms.CharField()


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

    def test_renter_template(self):
        form = MockMontrekReportForm()
        test_html = form.to_html()
        self.assertEqual(
            test_html,
            '\n    <form method="post">\n    <fieldset>\n  <legend>Test</legend>\n  <input type="text" name="field_1" required id="id_field_1">\n</fieldset>\n\n    <button type="submit" class="btn btn-default">Submit</button>\n    </form>\n            ',
        )

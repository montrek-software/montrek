from django.test import TestCase
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

    def test_renter_template(self):
        form = MockMontrekReportForm()
        test_html = form.to_html()
        self.assertEqual(
            test_html.replace(" ", ""),
            '<form method="post" class="tile">\n  <fieldset>\n  <legend>Test</legend>\n  <input type="text" name="field_1" required id="id_field_1">\n</fieldset>\n\n    <button type="submit" class="btn btn-custom">Submit</button>\n    </form>\n'.replace(
                " ", ""
            ),
        )

from django.test import TestCase
from reporting.forms import MontrekReportForm


class MockNoTemplateMontrekReportForm(MontrekReportForm): ...


class TestMontrekReportForm(TestCase):
    def test_no_template(self):
        self.assertRaises(
            NotImplementedError,
            MockNoTemplateMontrekReportForm().to_html,
        )

from django.test import TestCase
from reporting.core.reporting_data import ReportingData


class TestReportingData(TestCase):
    def test_raise_error_when_no_df_or_graph_given(self):
        self.assertRaises(ValueError, ReportingData, title="Test Title")

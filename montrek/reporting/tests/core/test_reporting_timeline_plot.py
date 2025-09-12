import pandas as pd
from django.test import TestCase
from reporting.core.reporting_data import ReportingTimelineData
from reporting.core.reporting_timeline_plot import ReportingTimelinePlot


class TestReportingTimelinePlot(TestCase):
    def test_timeline_plot(self):
        tl_df = pd.DataFrame(
            {
                "start_date": ["2025-10-12", "2025-10-19"],
                "end_date": ["2025-10-19", "2025-10-26"],
                "topic": ["step_1", "step_2"],
            }
        )
        report_data = ReportingTimelineData(title="Test Timeline", timeline_df=tl_df)
        timeline_plot = ReportingTimelinePlot()
        timeline_plot.generate(report_data)

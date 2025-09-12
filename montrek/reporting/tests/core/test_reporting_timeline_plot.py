import numpy as np
import pandas as pd
import plotly.io as pio
from django.test import TestCase
from reporting.core.reporting_data import ReportingTimelineData
from reporting.core.reporting_timeline_plot import ReportingTimelinePlot


class TestReportingTimelinePlot(TestCase):
    def setUp(self):
        tl_df = pd.DataFrame(
            {
                "start_date": ["2025-10-12", "2025-10-19"],
                "end_date": ["2025-10-19", "2025-10-26"],
                "topic": ["step_1", "step_2"],
            }
        )
        report_data = ReportingTimelineData(
            title="Test Timeline",
            timeline_df=tl_df,
            item_name_col="topic",
            start_date_col="start_date",
            end_date_col="end_date",
        )
        timeline_plot = ReportingTimelinePlot()
        timeline_plot.generate(report_data)
        self.fig = timeline_plot.figure

    def test_single_horizontal_bar_trace(self):
        self.assertEqual(len(self.fig.data), 1)
        tr = self.fig.data[0]
        self.assertEqual(tr.type, "bar")
        self.assertEqual(tr.orientation, "h")
        self.assertFalse(tr.showlegend)
        self.assertFalse(self.fig.layout.showlegend)

    def test_axes_and_title(self):
        self.assertEqual(self.fig.layout.title.text, "Test Timeline")
        self.assertEqual(self.fig.layout.xaxis.type, "date")
        # y-axis title is empty ({}), so .text is typically None
        self.assertTrue(
            getattr(self.fig.layout.yaxis.title, "text", None) in (None, "")
        )

    def test_categories_and_bases(self):
        tr = self.fig.data[0]
        np.testing.assert_array_equal(
            tr.y, np.array(["step_1", "step_2"], dtype=object)
        )
        # base carries start dates as strings that Plotly can parse
        self.assertEqual(list(tr.base), ["2025-10-12", "2025-10-19"])

    def test_durations_are_7_days_in_ms(self):
        tr = self.fig.data[0]
        # You printed x as ~6.048e+08; that's 7 days in milliseconds.
        # 7 days in ms:
        seven_days_ms = 7 * 24 * 60 * 60 * 1000  # 604_800_000
        self.assertTrue(np.array_equal(tr.x.astype(float), seven_days_ms))

    def test_hovertemplate_exact(self):
        tr = self.fig.data[0]
        self.assertEqual(
            tr.hovertemplate,
            "start_date=%{base}<br>end_date=%{x}<br>topic=%{y}<extra></extra>",
        )

    def test_styling_consistency(self):
        tr = self.fig.data[0]
        # Bar color and font color as shown
        self.assertEqual(tr.marker.color, "#004767")
        self.assertEqual(self.fig.layout.font.color, "#004767")
        # Backgrounds per layout
        self.assertEqual(self.fig.layout.paper_bgcolor, "#FFFFFF")
        self.assertEqual(self.fig.layout.plot_bgcolor, "#FFFFFF")
        # barmode overlay
        self.assertEqual(self.fig.layout.barmode, "overlay")
        # text position on bars
        self.assertEqual(tr.textposition, "auto")

    def test_alignment_and_grouping_fields_present(self):
        tr = self.fig.data[0]
        # Presence/values as printed
        self.assertEqual(getattr(tr, "alignmentgroup", None), "True")
        self.assertEqual(getattr(tr, "legendgroup", ""), "")
        self.assertEqual(getattr(tr, "offsetgroup", ""), "")

    def test_json_serializable(self):
        # Should not raise
        _ = pio.to_json(self.fig)

    def test_dates_parse_cleanly_and_end_after_start(self):
        """Optional: verifies that base + duration imply valid end timestamps."""
        tr = self.fig.data[0]

        starts = pd.to_datetime(list(tr.base), utc=True)
        # x provided in milliseconds; convert to Timedelta
        durations = pd.to_timedelta(tr.x.astype(float), unit="ms")
        ends = starts + durations

        # Sanity: all durations positive and end >= start
        self.assertTrue((durations > pd.Timedelta(0)).all())
        self.assertTrue((ends >= starts).all())

        # Spot-check first bar spans exactly 7 days
        self.assertEqual((ends[0] - starts[0]), pd.Timedelta(days=7))

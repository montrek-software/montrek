from datetime import date
from unittest.mock import patch
import numpy as np
import pandas as pd
import plotly.io as pio
from django.test import TestCase
from reporting.core.reporting_colors import ReportingColors
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
            bar_color=ReportingColors.BLUE.hex,
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
        self.assertEqual(len(self.fig.layout.shapes), 0)
        self.assertFalse(self.fig.layout.showlegend)
        self.assertNotEqual(self.fig.layout.yaxis.autorange, "reversed")

    def test_axes_and_title(self):
        self.assertEqual(self.fig.layout.title.text, "Test Timeline")
        self.assertEqual(self.fig.layout.xaxis.type, "date")
        # y-axis title is empty ({}), so .text is typically None
        self.assertTrue(
            getattr(self.fig.layout.yaxis.title, "text", None) in (None, "")
        )

    def test_categories_and_bases(self):
        tr = self.fig.data[0]
        # Default reversed_order=False uses ascending=False, so latest start_date first.
        np.testing.assert_array_equal(
            tr.y, np.array(["step_2", "step_1"], dtype=object)
        )
        # base carries start dates in the same sorted order
        dates_list = [np.datetime_as_string(fdate, unit="D") for fdate in tr.base]
        self.assertEqual(dates_list, ["2025-10-19", "2025-10-12"])

    def test_durations_are_7_days_in_ms(self):
        tr = self.fig.data[0]
        # You printed x as ~6.048e+08; that's 7 days in milliseconds.
        # 7 days in ms:
        seven_days_ms = 7 * 24 * 60 * 60 * 1000  # 604_800_000
        self.assertTrue(np.allclose(tr.x.astype(float), seven_days_ms, rtol=0, atol=0))

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
        self.assertEqual(getattr(tr, "legendgroup", ""), "")

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

    def test_invalid_data__no_df(self):
        tl_df = "Something wrong"
        report_data = ReportingTimelineData(
            title="Test Timeline",
            timeline_df=tl_df,
            item_name_col="topic",
            start_date_col="start_date",
            end_date_col="end_date",
        )
        timeline_plot = ReportingTimelinePlot()
        self.assertRaises(ValueError, timeline_plot.generate, report_data)

    def test_invalid_data__wrong_cols(self):
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
            item_name_col="schopic",
            start_date_col="start_date",
            end_date_col="end_date",
        )
        timeline_plot = ReportingTimelinePlot()
        self.assertRaises(ValueError, timeline_plot.generate, report_data)

    def test_invalid_data__wrong_item_col_type(self):
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
            item_name_col=15,
            start_date_col="start_date",
            end_date_col="end_date",
        )
        timeline_plot = ReportingTimelinePlot()
        self.assertRaises(ValueError, timeline_plot.generate, report_data)


class TestAdditionalTimelineFeatures(TestCase):
    def test_timeline_plot__with_report_date(self):
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
            report_date=date(2025, 10, 18),
        )
        timeline_plot = ReportingTimelinePlot()
        timeline_plot.generate(report_data)
        fig = timeline_plot.figure
        # Verify a vertical line shape was added
        shapes = fig.layout.shapes
        self.assertEqual(len(shapes), 1)

        vline = shapes[0]
        self.assertEqual(vline.type, "line")
        self.assertEqual(vline.x0, vline.x1)  # x0 == x1 confirms it's vertical

        # Verify it's positioned at the correct date
        # add_vline stores the x value as a millisecond timestamp internally
        expected_report_date = date(2025, 10, 18)
        vline_date = vline.x0
        self.assertEqual(vline_date, expected_report_date)

    def test_timeline_plot__raise_error_wrong_report_date_type(self):
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
            report_date=[date(2025, 10, 18)],
        )
        timeline_plot = ReportingTimelinePlot()
        self.assertRaises(TypeError, timeline_plot.generate, report_data)


class TestColorAdjustability(TestCase):
    _TL_DF = pd.DataFrame(
        {
            "start_date": ["2025-10-12", "2025-10-19"],
            "end_date": ["2025-10-19", "2025-10-26"],
            "topic": ["step_1", "step_2"],
            "category": ["A", "B"],
        }
    )

    def _make_fig(self, **kwargs):
        report_data = ReportingTimelineData(
            title="Color Test",
            timeline_df=self._TL_DF.copy(),
            item_name_col="topic",
            start_date_col="start_date",
            end_date_col="end_date",
            **kwargs,
        )
        plot = ReportingTimelinePlot()
        plot.generate(report_data)
        return plot.figure

    def test_custom_bar_color_is_applied(self):
        fig = self._make_fig(bar_color="#FF0000")
        self.assertEqual(fig.data[0].marker.color, "#FF0000")

    def test_default_bar_color_uses_primary_light(self):
        with patch(
            "reporting.core.reporting_timeline_plot.get_color",
            return_value="#AABBCC",
        ) as mock_get_color:
            fig = self._make_fig()
        mock_get_color.assert_called_once_with("primary_light")
        self.assertEqual(fig.data[0].marker.color, "#AABBCC")

    def test_bar_color_ignored_when_color_col_set(self):
        # When color_col is used, Plotly manages per-category colours;
        # update_traces must NOT override them with a single bar_color.
        color_map = {"A": "#111111", "B": "#222222"}
        fig = self._make_fig(
            color_col="category",
            color_descrete_map=color_map,
            bar_color="#FF0000",
        )
        # There are two traces (one per category); neither should be #FF0000.
        for trace in fig.data:
            self.assertNotEqual(trace.marker.color, "#FF0000")

    def test_custom_vline_color_is_applied(self):
        fig = self._make_fig(
            report_date=date(2025, 10, 15),
            vline_color="#00FF00",
        )
        self.assertEqual(len(fig.layout.shapes), 1)
        self.assertEqual(fig.layout.shapes[0].line.color, "#00FF00")

    def test_default_vline_color_is_red(self):
        fig = self._make_fig(report_date=date(2025, 10, 15))
        self.assertEqual(len(fig.layout.shapes), 1)
        self.assertEqual(fig.layout.shapes[0].line.color, ReportingColors.RED.hex)

    def test_no_vline_when_report_date_is_none(self):
        fig = self._make_fig(vline_color="#00FF00")
        self.assertEqual(len(fig.layout.shapes), 0)

    def test_color_col_with_discrete_map(self):
        color_map = {"A": "#AAAAAA", "B": "#BBBBBB"}
        fig = self._make_fig(
            color_col="category",
            color_descrete_map=color_map,
        )
        # Each category gets its own trace.
        self.assertEqual(len(fig.data), 2)
        self.assertFalse(fig.layout.showlegend)

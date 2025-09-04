import pandas as pd
import plotly.graph_objects as go
from django.test import TestCase
from reporting.constants import ReportingPlotType
from reporting.core.reporting_data import ReportingData
from reporting.core.reporting_plots import ReportingPlot


class TestReportingPlots(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_df = pd.DataFrame(
            {
                "Category": ["A", "B", "C", "D"],
                "Value": [10, 25, 15, 30],
                "ValueLine": [15, 20, 10, 40],
            }
        )

    def test_reporting_plots_y_axis_and_types_do_not_match(self):
        reporting_data = ReportingData(
            data_df=self.test_df,
            x_axis_column="Category",
            y_axis_columns=["Value", "ValueLine"],
            plot_types=[ReportingPlotType.BAR],
            title="Test Plot",
        )
        with self.assertRaises(ValueError) as error:
            ReportingPlot().generate(reporting_data)
        self.assertEqual(
            str(error.exception), "Number of y_axis_columns and plot_types must match"
        )

    def test_reporting_plots_none_type_not_supported(self):
        reporting_data = ReportingData(
            data_df=self.test_df,
            x_axis_column="Category",
            y_axis_columns=["Value"],
            plot_types=[ReportingPlotType.NONE],
            title="Test Plot",
        )
        with self.assertRaises(ValueError) as error:
            ReportingPlot().generate(reporting_data)
        self.assertEqual(
            str(error.exception), "Plot type ReportingPlotType.NONE not supported"
        )

    def test_reporting_plots_neither_index_nor_xaxis(self):
        reporting_data = ReportingData(
            data_df=self.test_df,
            y_axis_columns=["Value"],
            plot_types=[ReportingPlotType.BAR],
            title="Test Plot",
        )
        with self.assertRaises(ValueError) as error:
            ReportingPlot().generate(reporting_data)
        self.assertEqual(
            str(error.exception),
            "x_axis_column must be provided if x_axis_is_index is False",
        )

    def test_reporting_plots_bar_line(self):
        reporting_data = ReportingData(
            data_df=self.test_df,
            x_axis_column="Category",
            y_axis_columns=["Value", "ValueLine"],
            plot_types=[ReportingPlotType.BAR, ReportingPlotType.LINE],
            title="Test Plot",
        )
        reporting_plot = ReportingPlot()
        reporting_plot.generate(reporting_data)
        self.assertTrue(isinstance(reporting_plot.figure, go.Figure))
        self.assertEqual(len(reporting_plot.figure.data), 2)
        self.assertEqual(reporting_plot.figure.data[0].type, "bar")
        self.assertEqual(reporting_plot.figure.data[1].type, "scatter")
        self.assertTrue(isinstance(reporting_plot.figure.data[0], go.Bar))
        self.assertTrue(isinstance(reporting_plot.figure.data[1], go.Scatter))
        self.assertEqual(reporting_plot.figure.data[0].x.tolist(), ["A", "B", "C", "D"])
        self.assertEqual(reporting_plot.figure.data[0].y.tolist(), [10, 25, 15, 30])
        self.assertEqual(reporting_plot.figure.data[1].x.tolist(), ["A", "B", "C", "D"])
        self.assertEqual(reporting_plot.figure.data[1].y.tolist(), [15, 20, 10, 40])
        reporting_plot_html = reporting_plot.to_html()
        self.assertTrue(reporting_plot_html.startswith("<div>"))
        self.assertTrue(reporting_plot_html.endswith("</div>"))
        reporting_plot_json = reporting_plot.to_json()
        self.assertTrue("reporting_plot" in reporting_plot_json.keys())

    def test_reporting_plots_line_stacked(self):
        reporting_data = ReportingData(
            data_df=self.test_df,
            x_axis_column="Category",
            y_axis_columns=["Value", "ValueLine"],
            plot_types=[ReportingPlotType.LINE, ReportingPlotType.LINESTACK],
            title="Test Plot",
        )
        reporting_plot = ReportingPlot()
        reporting_plot.generate(reporting_data)
        self.assertTrue(isinstance(reporting_plot.figure, go.Figure))
        self.assertEqual(len(reporting_plot.figure.data), 2)
        self.assertEqual(reporting_plot.figure.data[0].type, "scatter")
        self.assertEqual(reporting_plot.figure.data[1].type, "scatter")
        self.assertTrue(isinstance(reporting_plot.figure.data[0], go.Scatter))
        self.assertTrue(isinstance(reporting_plot.figure.data[1], go.Scatter))
        self.assertEqual(reporting_plot.figure.data[0].x.tolist(), ["A", "B", "C", "D"])
        self.assertEqual(reporting_plot.figure.data[0].y.tolist(), [10, 25, 15, 30])
        self.assertEqual(reporting_plot.figure.data[1].x.tolist(), ["A", "B", "C", "D"])
        self.assertEqual(reporting_plot.figure.data[1].y.tolist(), [25, 45, 25, 70])
        reporting_plot_html = reporting_plot.to_html()
        self.assertTrue(reporting_plot_html.startswith("<div>"))
        self.assertTrue(reporting_plot_html.endswith("</div>"))
        reporting_plot_json = reporting_plot.to_json()
        self.assertTrue("reporting_plot" in reporting_plot_json.keys())

    def test_reporting_plots_line_stacked__str_call(self):
        reporting_data = ReportingData(
            data_df=self.test_df,
            x_axis_column="Category",
            y_axis_columns=["Value", "ValueLine"],
            plot_types=["line", "linestack"],
            title="Test Plot",
        )
        reporting_plot = ReportingPlot()
        reporting_plot.generate(reporting_data)
        self.assertTrue(isinstance(reporting_plot.figure, go.Figure))
        self.assertEqual(len(reporting_plot.figure.data), 2)
        self.assertEqual(reporting_plot.figure.data[0].type, "scatter")
        self.assertEqual(reporting_plot.figure.data[1].type, "scatter")
        self.assertTrue(isinstance(reporting_plot.figure.data[0], go.Scatter))
        self.assertTrue(isinstance(reporting_plot.figure.data[1], go.Scatter))
        self.assertEqual(reporting_plot.figure.data[0].x.tolist(), ["A", "B", "C", "D"])
        self.assertEqual(reporting_plot.figure.data[0].y.tolist(), [10, 25, 15, 30])
        self.assertEqual(reporting_plot.figure.data[1].x.tolist(), ["A", "B", "C", "D"])
        self.assertEqual(reporting_plot.figure.data[1].y.tolist(), [25, 45, 25, 70])
        reporting_plot_html = reporting_plot.to_html()
        self.assertTrue(reporting_plot_html.startswith("<div>"))
        self.assertTrue(reporting_plot_html.endswith("</div>"))

    def test_reporting_plots__plot_parameters(self):
        reporting_data = ReportingData(
            data_df=self.test_df,
            x_axis_column="Category",
            y_axis_columns=["Value", "ValueLine"],
            plot_types=["line", "line"],
            title="Test Plot",
            plot_parameters=[{"fill": "tozeroy"}, {"fill": "tonexty"}],
        )
        reporting_plot = ReportingPlot()
        reporting_plot.generate(reporting_data)
        self.assertEqual(reporting_plot.figure.data[0].fill, "tozeroy")
        self.assertEqual(reporting_plot.figure.data[1].fill, "tonexty")

    def test_set_x_axis(self):
        test_df = pd.DataFrame(
            {
                "Category": ["A", "B", "C", "D"],
                "Value": [10, 25, 15, 30],
            },
        )
        reporting_data = ReportingData(
            data_df=test_df,
            x_axis_column="Category",
            y_axis_columns=["Value"],
            plot_types=[ReportingPlotType.BAR],
            title="Test Plot",
        )
        reporting_plot = ReportingPlot()
        test_x = reporting_plot._set_x_axis(reporting_data)
        self.assertEqual(test_x.tolist(), ["A", "B", "C", "D"])

    def test_set_x_axis_index(self):
        test_df = pd.DataFrame(
            {
                "Value": [10, 25, 15, 30],
            },
            index=["A", "B", "C", "D"],
        )
        reporting_data = ReportingData(
            data_df=test_df,
            x_axis_is_index=True,
            y_axis_columns=["Value"],
            plot_types=[ReportingPlotType.BAR],
            title="Test Plot",
        )
        reporting_plot = ReportingPlot()
        test_x = reporting_plot._set_x_axis(reporting_data)
        self.assertEqual(test_x.tolist(), ["A", "B", "C", "D"])

    def test_set_plot_types_valid(self):
        test_plot_types = [
            ReportingPlotType.BAR,
            ReportingPlotType.LINE,
            "bar",
            "liNE",
            "pie",
        ]
        expected_plot_types = [
            ReportingPlotType.BAR,
            ReportingPlotType.LINE,
            ReportingPlotType.BAR,
            ReportingPlotType.LINE,
            ReportingPlotType.PIE,
        ]
        reporting_data = ReportingData(
            data_df=pd.DataFrame(),
            plot_types=test_plot_types,
            title="Test Plot",
        )
        reporting_plot = ReportingPlot()
        result_plot_types = reporting_plot._set_plot_types(reporting_data)
        self.assertEqual(result_plot_types, expected_plot_types)


class TestReportingPiePlots(TestCase):
    def test_pie_plots(self):
        test_df = pd.DataFrame(
            {
                "Category": ["A", "B", "C", "D"],
                "Value": [10, 25, 15, 30],
            },
        )
        reporting_data = ReportingData(
            data_df=test_df,
            x_axis_column="Category",
            y_axis_columns=["Value"],
            plot_types=[ReportingPlotType.PIE],
            title="Test Plot",
        )
        reporting_plot = ReportingPlot()
        reporting_plot.generate(reporting_data)
        self.assertTrue(isinstance(reporting_plot.figure, go.Figure))
        self.assertEqual(len(reporting_plot.figure.data), 1)
        self.assertEqual(reporting_plot.figure.data[0].type, "pie")
        self.assertTrue(isinstance(reporting_plot.figure.data[0], go.Pie))
        self.assertEqual(
            reporting_plot.figure.data[0].labels.tolist(), ["A", "B", "C", "D"]
        )
        self.assertEqual(
            reporting_plot.figure.data[0].values.tolist(), [10, 25, 15, 30]
        )
        reporting_plot_html = reporting_plot.to_html()
        self.assertTrue(reporting_plot_html.startswith("<div>"))
        self.assertTrue(reporting_plot_html.endswith("</div>"))
        reporting_plot_latex = reporting_plot.to_latex()
        self.assertTrue(reporting_plot_latex.startswith("\\begin{figure}"))
        reporting_plot_json = reporting_plot.to_json()
        self.assertTrue("reporting_plot" in reporting_plot_json.keys())

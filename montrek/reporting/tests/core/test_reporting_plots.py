import pandas as pd
import plotly.graph_objects as go
from django.test import TestCase
from reporting.core.reporting_plots import ReportingPlot
from reporting.core.reporting_data import ReportingData
from reporting.constants import ReportingPlotType

class TestReportingPlots(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_df = pd.DataFrame(
            {'Category': ['A', 'B', 'C', 'D'],
             'Value': [10, 25, 15, 30],
             'ValueLine': [15,20,10,40],
            })

    def test_reporting_plots_y_axis_and_types_do_not_match(self):
        reporting_data = ReportingData(
                    data_df=self.test_df,
                    x_axis_column='Category',
                    y_axis_columns=['Value', 'ValueLine'],
                    plot_types=[ReportingPlotType.BAR]
        )    
        with self.assertRaises(ValueError):
            ReportingPlot().generate(
                reporting_data
            )

    def test_reporting_plots_none_type_not_supported(self):
        reporting_data = ReportingData(
                    data_df=self.test_df,
                    x_axis_column='Category',
                    y_axis_columns=['Value'],
                    plot_types=[ReportingPlotType.NONE]
        )    
        with self.assertRaises(ValueError):
            ReportingPlot().generate(
                reporting_data
            )

    def test_reporting_plots_bar_line(self):
        reporting_data = ReportingData(
                    data_df=self.test_df,
                    x_axis_column='Category',
                    y_axis_columns=['Value', 'ValueLine'],
                    plot_types=[ReportingPlotType.BAR, ReportingPlotType.LINE]
        )    
        reporting_plot = ReportingPlot()
        reporting_plot.generate(
            reporting_data
        )
        self.assertTrue(isinstance(reporting_plot.figure, go.Figure))
        self.assertEqual(len(reporting_plot.figure.data), 2)
        self.assertEqual(reporting_plot.figure.data[0].type, 'bar')
        self.assertEqual(reporting_plot.figure.data[1].type, 'scatter')
        self.assertTrue(isinstance(reporting_plot.figure.data[0], go.Bar))
        self.assertTrue(isinstance(reporting_plot.figure.data[1], go.Scatter))
        self.assertEqual(reporting_plot.figure.data[0].x.tolist(), ['A', 'B', 'C', 'D'])
        self.assertEqual(reporting_plot.figure.data[0].y.tolist(), [10, 25, 15, 30])
        self.assertEqual(reporting_plot.figure.data[1].x.tolist(), ['A', 'B', 'C', 'D'])
        self.assertEqual(reporting_plot.figure.data[1].y.tolist(), [15, 20, 10, 40])
        reporting_plot_html = reporting_plot.format_html()
        self.assertTrue(reporting_plot_html.startswith('<div>'))
        self.assertTrue(reporting_plot_html.endswith('</div>'))


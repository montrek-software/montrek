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
        with self.assertRaises(ValueError) as e:
            ReportingPlot().generate(
                reporting_data
            )
        self.assertEqual(str(e.exception), "Number of y_axis_columns and plot_types must match")


    def test_reporting_plots_none_type_not_supported(self):
        reporting_data = ReportingData(
                    data_df=self.test_df,
                    x_axis_column='Category',
                    y_axis_columns=['Value'],
                    plot_types=[ReportingPlotType.NONE]
        )    
        with self.assertRaises(ValueError) as e:
            ReportingPlot().generate(
                reporting_data
            )
        self.assertEqual(str(e.exception), "Plot type ReportingPlotType.NONE not supported")

    def test_reporting_plots_neither_index_nor_xaxis(self):
        reporting_data = ReportingData(
                    data_df=self.test_df,
                    y_axis_columns=['Value'],
                    plot_types=[ReportingPlotType.BAR]
        )    
        with self.assertRaises(ValueError) as e:
            ReportingPlot().generate(
                reporting_data
            )
        self.assertEqual(str(e.exception), "x_axis_column must be provided if x_axis_is_index is False")

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

    def test_set_x_axis(self):
        test_df = pd.DataFrame(
            {'Category': ['A', 'B', 'C', 'D'],
             'Value': [10, 25, 15, 30],
            },
        )
        reporting_data = ReportingData(
                    data_df=test_df,
                    x_axis_column='Category',
                    y_axis_columns=['Value'],
                    plot_types=[ReportingPlotType.BAR]
        )    
        reporting_plot = ReportingPlot()
        test_x = reporting_plot._set_x_axis(reporting_data)
        self.assertEqual(test_x.tolist(), ['A', 'B', 'C', 'D'])
        
    def test_set_x_axis_index(self):
        test_df = pd.DataFrame(
            {
             'Value': [10, 25, 15, 30],
            },
            index=['A', 'B', 'C', 'D']
        )
        reporting_data = ReportingData(
                    data_df=test_df,
                    x_axis_is_index=True,
                    y_axis_columns=['Value'],
                    plot_types=[ReportingPlotType.BAR]
        )    
        reporting_plot = ReportingPlot()
        test_x = reporting_plot._set_x_axis(reporting_data)
        self.assertEqual(test_x.tolist(), ['A', 'B', 'C', 'D'])

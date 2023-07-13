import pandas as pd
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
                    data=self.test_df,
                    x_axis_column='Category',
                    y_axis_columns=['Value', 'ValueLine'],
                    plot_types=[ReportingPlotType.BAR]
        )    
        with self.assertRaises(ValueError):
            ReportingPlot().generate(
                reporting_data
            )


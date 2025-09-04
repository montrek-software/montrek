from django.test import TestCase
from networkx import DiGraph
from plotly.graph_objs import Scatter
from reporting.core.reporting_data import ReportingNetworkData
from reporting.core.reporting_network_plots import ReportingNetworkPlot


class TestReportingNetworkPlot(TestCase):
    def test_generate_network_plot(self):
        graph = DiGraph()
        graph.add_node("A")
        graph.add_node("B")
        graph.add_edge("A", "B")

        reporting_data = ReportingNetworkData(graph=graph, title="Test Network Graph")

        reporting_plot = ReportingNetworkPlot()
        reporting_plot.generate(reporting_data)
        self.assertTrue(
            all([isinstance(plot, Scatter) for plot in reporting_plot.figure.data])
        )

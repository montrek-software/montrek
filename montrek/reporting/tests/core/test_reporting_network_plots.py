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
        figure_data = reporting_plot.figure.data
        self.assertTrue(all([isinstance(plot, Scatter) for plot in figure_data]))
        edges = figure_data[0]
        nodes = figure_data[1]
        self.assertEqual(edges["mode"], "lines")
        self.assertEqual(nodes["mode"], "markers+text")
        self.assertEqual(nodes["text"], ("<b>A</b>", "<b>B</b>"))

    def test_generate_network_plot__with_marker(self):
        graph = DiGraph()
        graph.add_node("A", marker_att="A")
        graph.add_node("B", marker_att="B")
        graph.add_edge("A", "B")

        marker_map = {"A": "circle", "B": "square"}

        reporting_data = ReportingNetworkData(
            graph=graph,
            title="Test Network Graph",
            symbol_attr="marker_att",
            symbol_map=marker_map,
        )

        reporting_plot = ReportingNetworkPlot()
        reporting_plot.generate(reporting_data)
        figure_data = reporting_plot.figure.data
        self.assertEqual(figure_data[1]["marker"]["symbol"], ("circle", "square"))

    def test_generate_network_plot__marker_properties(self):
        graph = DiGraph()
        graph.add_node("A")
        graph.add_node("B")
        graph.add_edge("A", "B")

        reporting_data = ReportingNetworkData(
            graph=graph, title="Test Network Graph", marker_size=30, marker_line_width=3
        )

        reporting_plot = ReportingNetworkPlot()
        reporting_plot.generate(reporting_data)
        figure_data = reporting_plot.figure.data
        self.assertEqual(figure_data[1]["marker"]["size"], 30)
        self.assertEqual(figure_data[1]["marker"]["line"]["width"], 3)

    def test_generate_network_plot__group_colors(self):
        graph = DiGraph()
        graph.add_node("A", group="AA")
        graph.add_node("B", group="BB")
        graph.add_edge("A", "B")

        reporting_data = ReportingNetworkData(
            graph=graph, title="Test Network Graph", group_attr="group"
        )

        reporting_plot = ReportingNetworkPlot()
        reporting_plot.generate(reporting_data)
        figure_data = reporting_plot.figure.data
        self.assertIn("#BE0D3E", figure_data[1]["marker"]["color"])
        self.assertIn("#004767", figure_data[1]["marker"]["color"])

    def test_reporting_network_plot__left_to_right_layout(self):
        graph = DiGraph()
        graph.add_node("A")
        graph.add_node("B")
        graph.add_edge("A", "B")

        reporting_data = ReportingNetworkData(
            graph=graph, title="Test Network Graph", layout="LR"
        )
        reporting_plot = ReportingNetworkPlot()
        reporting_plot.generate(reporting_data)

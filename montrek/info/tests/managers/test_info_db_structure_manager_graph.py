import os

import networkx as nx
from django.conf import settings
from django.test import TestCase
from info.managers.info_db_structure_manager import InfoDbStructureManager


class TestInfoDbStructureManagerGraph(TestCase):
    def setUp(self):
        self.manager = InfoDbStructureManager()
        self.db_structure_container = self.manager.get_db_structure_container()
        self.graph = self.manager.to_networkx_graph(self.db_structure_container)

    def test_save_graph_as_png(self):
        filename = "test_db_structure.png"
        self.manager.save_graph_as_png(self.graph, filename)
        path = settings.MEDIA_ROOT + filename
        self.assertTrue(os.path.exists(path))
        os.remove(path)
        self.assertIsInstance(self.graph, nx.DiGraph)

    def test_graph_nodes(self):
        expected_nodes = {
            "TestHubA": {"type": "hub", "app": "info"},
            "TestHubB": {"type": "hub", "app": "info"},
            "TestHubValueDateA": {"type": "hub_value_date", "app": "info"},
            "TestHubValueDateB": {"type": "hub_value_date", "app": "info"},
            "TestSatA1": {"type": "satellite", "app": "info"},
            "TestSatA2": {"type": "satellite", "app": "info"},
            "TestSatB1": {"type": "satellite", "app": "info"},
            "TestSatB2": {"type": "satellite", "app": "info"},
            "TestSatTSB1": {"type": "time_series_satellite", "app": "info"},
            "TestSatTSB2": {"type": "time_series_satellite", "app": "info"},
            "LinkTestHubATestHubB": {"type": "link", "app": "info"},
        }
        for node, attrs in expected_nodes.items():
            self.assertIn(node, self.graph.nodes)
            self.assertEqual(self.graph.nodes[node], attrs)

    def test_graph_edges(self):
        expected_edges = [
            ("TestHubA", "TestHubValueDateA"),
            ("TestHubB", "TestHubValueDateB"),
            ("TestHubA", "TestSatA1"),
            ("TestHubA", "TestSatA2"),
            ("TestHubB", "TestSatB1"),
            ("TestHubB", "TestSatB2"),
            ("TestHubValueDateB", "TestSatTSB1"),
            ("TestHubValueDateB", "TestSatTSB2"),
            ("TestHubA", "LinkTestHubATestHubB"),
            ("LinkTestHubATestHubB", "TestHubB"),
        ]
        for edge in expected_edges:
            self.assertIn(edge, self.graph.edges)

import networkx as nx
from django.test import SimpleTestCase

# Adjust this import to where you put layered_pos
from reporting.core.network_layouts.utils import layered_pos


def _round_tuple(t, ndigits=6):
    return (round(float(t[0]), ndigits), round(float(t[1]), ndigits))


class TestLayeredPos(SimpleTestCase):
    def test_dag_top_to_bottom_horizontal_align(self):
        """
        For a DAG with layers by topological generations:
        - align='horizontal' => ranks differ in Y (top→bottom),
          nodes in same rank share (approximately) the same Y.
        """
        G = nx.DiGraph()
        G.add_edges_from(
            [
                ("Start", "A"),
                ("Start", "B"),
                ("A", "C"),
                ("B", "C"),
                ("C", "D"),
                ("C", "E"),
            ]
        )

        pos = layered_pos(G, align="horizontal")
        self.assertTrue(pos, "Expected non-empty positions dict")
        # Round to avoid tiny float noise
        pos = {n: _round_tuple(p, 6) for n, p in pos.items()}

        # Compute expected layers via topological generations (same as function uses for DAGs)
        expected_layers = {
            n: i for i, gen in enumerate(nx.topological_generations(G)) for n in gen
        }

        # Group nodes by expected layer and check Y is (approximately) constant per layer,
        # and strictly increasing with layer index.
        layer_to_y = {}
        for n, layer in expected_layers.items():
            _, y = pos[n]
            layer_to_y.setdefault(layer, set()).add(y)

        # Each layer should collapse to ~one Y value
        for layer, ys in layer_to_y.items():
            with self.subTest(layer=layer):
                self.assertLessEqual(len(ys), 2, "Y varies too much within a layer")

        # Y should increase with layer
        sorted_layers = sorted(layer_to_y)
        ys_in_order = [sorted(list(layer_to_y[L]))[0] for L in sorted_layers]
        self.assertEqual(ys_in_order, sorted(ys_in_order), "Y should increase by layer")

    def test_dag_left_to_right_vertical_align(self):
        """
        align='vertical' => ranks differ in X (left→right),
        nodes in same rank share approx the same X.
        """
        G = nx.DiGraph()
        G.add_edges_from([("S", "A"), ("S", "B"), ("A", "C"), ("B", "C")])

        pos = layered_pos(G, align="vertical")
        pos = {n: _round_tuple(p, 6) for n, p in pos.items()}

        expected_layers = {
            n: i for i, gen in enumerate(nx.topological_generations(G)) for n in gen
        }

        layer_to_x = {}
        for n, layer in expected_layers.items():
            x, _ = pos[n]
            layer_to_x.setdefault(layer, set()).add(x)

        for layer, xs in layer_to_x.items():
            with self.subTest(layer=layer):
                self.assertLessEqual(len(xs), 2, "X varies too much within a layer")

        sorted_layers = sorted(layer_to_x)
        xs_in_order = [sorted(list(layer_to_x[L]))[0] for L in sorted_layers]
        self.assertEqual(xs_in_order, sorted(xs_in_order), "X should increase by layer")

    def test_cycle_graph_bfs_layering_does_not_crash(self):
        """
        For cyclic graphs, the function falls back to BFS-style layering.
        We can't guarantee exact layers, but positions should be returned for all nodes
        and there should be multiple ranks (not all nodes stacked).
        """
        G = nx.DiGraph()
        # Insertion order helps keep layering stable for the test
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])  # 3-cycle

        pos_tb = layered_pos(G, align="horizontal")  # TB
        pos_lr = layered_pos(G, align="vertical")  # LR

        # All nodes must have positions in both orientations
        self.assertEqual(set(pos_tb.keys()), set(G.nodes()))
        self.assertEqual(set(pos_lr.keys()), set(G.nodes()))

        # Check there is at least more than one distinct coordinate along the layering axis
        ys = {round(p[1], 6) for p in pos_tb.values()}
        xs = {round(p[0], 6) for p in pos_lr.values()}
        self.assertGreater(len(ys), 1, "TB should have multiple ranks (distinct Y)")
        self.assertGreater(len(xs), 1, "LR should have multiple ranks (distinct X)")

    def test_isolated_nodes_get_positions(self):
        """
        Isolated or unreachable nodes should still receive coordinates.
        """
        G = nx.DiGraph()
        G.add_nodes_from(["X", "Y", "Z"])  # no edges

        pos = layered_pos(G, align="horizontal")
        self.assertEqual(set(pos.keys()), {"X", "Y", "Z"})
        for n in G:
            self.assertEqual(len(pos[n]), 2)
            # finite numbers
            self.assertTrue(all(map(lambda v: isinstance(v, (int, float)), pos[n])))

    def test_position_shape_and_types(self):
        """
        Basic contract: dict[node] -> (float, float)
        """
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3)])
        pos = layered_pos(G, align="horizontal")
        self.assertIsInstance(pos, dict)
        for n, p in pos.items():
            self.assertEqual(len(p), 2)
            self.assertTrue(all(isinstance(c, (int, float)) for c in p))

import math
from typing import Dict, Tuple

import networkx as nx
from django.test import SimpleTestCase

# 🔧 Change this import to your real module path:
from reporting.core.network_layouts import (
    LayoutKind,
    LRNetworkLayout,
    NetworkLayout,
    NetworkLayoutsFactory,
    SpringNetworkLayout,
    TBNetworkLayout,
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def make_small_digraph() -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_edges_from(
        [
            ("Expert Evaluation", "Report Section"),
            ("Topic A", "Report Section"),
            ("Report Section", "Type 1"),
            ("Report Section", "Type 2"),
            ("Expert Evaluation", "Fund X"),
        ]
    )
    return G


def span(pos: Dict[str, Tuple[float, float]]) -> Tuple[float, float]:
    xs = [xy[0] for xy in pos.values()]
    ys = [xy[1] for xy in pos.values()]
    return (max(xs) - min(xs), max(ys) - min(ys))


# ---------------------------------------------------------------------
# Factory behavior
# ---------------------------------------------------------------------
class TestNetworkLayoutsFactory(SimpleTestCase):
    def test_factory_alias_resolution(self):
        cases = [
            ("lr", LRNetworkLayout),
            ("LR", LRNetworkLayout),
            ("left_right", LRNetworkLayout),
            ("left-right", LRNetworkLayout),
            ("Left Right", LRNetworkLayout),  # spaces are ok
            ("graphviz_lr", LRNetworkLayout),
            ("tb", TBNetworkLayout),
            ("top_bottom", TBNetworkLayout),
            ("top-bottom", TBNetworkLayout),
            ("graphviz_tb", TBNetworkLayout),
            ("spring", SpringNetworkLayout),
            ("force", SpringNetworkLayout),
            ("force_directed", SpringNetworkLayout),
            ("force-directed", SpringNetworkLayout),
        ]
        for user_string, expected_cls in cases:
            with self.subTest(user_string=user_string):
                layout = NetworkLayoutsFactory.get(user_string)
                self.assertIsInstance(layout, NetworkLayout)
                self.assertIs(type(layout), expected_cls)

    def test_factory_returns_new_instances_each_time(self):
        a = NetworkLayoutsFactory.get("lr")
        b = NetworkLayoutsFactory.get("lr")
        self.assertIs(type(a), LRNetworkLayout)
        self.assertIs(type(b), LRNetworkLayout)
        self.assertIsNot(a, b)  # not a singleton

    def test_factory_rejects_empty_or_none(self):
        for bad in (None, ""):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError) as cm:
                    NetworkLayoutsFactory.get(bad)  # type: ignore[arg-type]
                self.assertIn("must be a non-empty string", str(cm.exception))

    def test_factory_unknown_layout_lists_all_options(self):
        with self.assertRaises(ValueError) as cm:
            NetworkLayoutsFactory.get("banana")
        msg = str(cm.exception)
        self.assertIn("Unknown layout 'banana'", msg)
        self.assertIn("Available layouts:", msg)

        # Ensure all declared aliases are mentioned
        all_aliases = {alias for kind in LayoutKind for alias in kind.value.aliases}
        for alias in all_aliases:
            self.assertIn(alias, msg)


# ---------------------------------------------------------------------
# Layout.pos() behavior
# ---------------------------------------------------------------------
class TestNetworkLayoutPos(SimpleTestCase):
    def test_spring_layout_pos_returns_mapping_and_is_deterministic(self):
        G = make_small_digraph()
        layout = SpringNetworkLayout()
        p1 = layout.pos(G)
        p2 = layout.pos(G)

        # Correct structure
        self.assertEqual(set(p1.keys()), set(G.nodes))
        for v in p1.values():
            self.assertEqual(len(v), 2)
            self.assertIsInstance(v[0], float)
            self.assertIsInstance(v[1], float)

        # Deterministic because seed=42 in implementation
        for n in G.nodes:
            x1, y1 = p1[n]
            x2, y2 = p2[n]
            self.assertTrue(math.isclose(x1, x2, rel_tol=0, abs_tol=1e-12))
            self.assertTrue(math.isclose(y1, y2, rel_tol=0, abs_tol=1e-12))

    def test_graphviz_lr_vs_tb_orientation_differs(self):
        G = make_small_digraph()

        lr = LRNetworkLayout().pos(G)
        tb = TBNetworkLayout().pos(G)

        sx_lr, sy_lr = span(lr)
        sx_tb, sy_tb = span(tb)

        self.assertGreater(sx_lr, sy_lr * 1.05)
        self.assertLess(sy_tb, sx_tb * 1.05)

        # Both return positions for all nodes
        self.assertEqual(set(lr.keys()), set(G.nodes))
        self.assertEqual(set(tb.keys()), set(G.nodes))


# ---------------------------------------------------------------------
# Normalization quirks
# ---------------------------------------------------------------------
class TestNormalizations(SimpleTestCase):
    def test_normalization_strips_whitespace_and_punctuation(self):
        cases = [
            ("  L R  ", LRNetworkLayout),
            ("Top  -  Bottom", TBNetworkLayout),
            ("FORCE  DIRECTED", SpringNetworkLayout),
            ("force_directed  ", SpringNetworkLayout),
        ]
        for weird, expected in cases:
            with self.subTest(inp=weird):
                layout = NetworkLayoutsFactory.get(weird)
                self.assertIs(type(layout), expected)

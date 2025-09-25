from collections import deque
from typing import Any, Hashable, Mapping

import networkx as nx
from networkx import DiGraph
from networkx.drawing.layout import multipartite_layout
from reporting.core.network_layouts.typing import Pos
from reporting.core.reporting_data import ReportingNetworkData

# ---------------------------
# Layering helpers
# ---------------------------


def _layers_by_topology(graph: DiGraph) -> dict[Hashable, int]:
    """Layer nodes by topological generations (for DAGs)."""
    return {
        n: i for i, gen in enumerate(nx.topological_generations(graph)) for n in gen
    }


def _layers_by_bfs(graph: DiGraph) -> dict[Hashable, int]:
    """
    Fallback layering using BFS from zero-in-degree roots (or an arbitrary node),
    with isolated nodes defaulted to layer 0.
    """
    roots = [n for n in graph if graph.in_degree(n) == 0] or [next(iter(graph.nodes))]
    layers: dict[Hashable, int] = {r: 0 for r in roots}

    dq: deque = deque(roots)
    while dq:
        u = dq.popleft()
        for v in graph.successors(u):
            if v not in layers:
                layers[v] = layers[u] + 1
                dq.append(v)

    # Ensure isolated nodes appear (e.g., components unreachable from chosen roots)
    for n in graph:
        layers.setdefault(n, 0)

    return layers


def _compute_layers(graph: DiGraph) -> dict[Hashable, int]:
    """Pick the best layering strategy based on whether the graph is a DAG."""
    return (
        _layers_by_topology(graph)
        if nx.is_directed_acyclic_graph(graph)
        else _layers_by_bfs(graph)
    )


# ---------------------------
# Attribute helpers
# ---------------------------


def _apply_subset_layers(graph: DiGraph, layers: Mapping[Hashable, int]) -> None:
    """Attach `subset` node attribute with layer indices."""
    nx.set_node_attributes(graph, dict(layers), "subset")


def _apply_grouped_subsets(
    graph: DiGraph,
    layers: Mapping[Hashable, int],
    group_attr: str,
) -> None:
    """
    If a grouping attribute is provided, use a (layer, group) tuple for `subset`.
    This preserves layered order while keeping groups distinct for multipartite_layout.
    """
    subsets: dict[Hashable, tuple[int, Any]] = {}
    for n, layer in layers.items():
        group_val = graph.nodes[n].get(group_attr, 0)
        subsets[n] = (layer, group_val)
    nx.set_node_attributes(graph, subsets, "subset")


# ---------------------------
# Layout helper
# ---------------------------


def _multipartite_positions(graph: DiGraph, align: str = "horizontal") -> Pos:
    """
    Compute positions with NetworkX multipartite_layout.
    align='horizontal' -> ranks stacked top→bottom (TB)
    align='vertical'   -> ranks side-by-side left→right (LR)
    """
    return multipartite_layout(graph, subset_key="subset", align=align, scale=1.0)


# ---------------------------
# Public API
# ---------------------------


def layered_pos(reporting_data: ReportingNetworkData, align: str = "horizontal") -> Pos:
    """
    Pure-Python layered positions:
      - align='horizontal' -> ranks stacked top→bottom (TB)
      - align='vertical'   -> ranks side-by-side left→right (LR)
    """
    graph = reporting_data.graph

    # 1) Compute layers
    layers = _compute_layers(graph)

    # 2) Attach subset attributes (layer-only or layer+group)
    if reporting_data.group_attr:
        _apply_grouped_subsets(graph, layers, reporting_data.group_attr)
    else:
        _apply_subset_layers(graph, layers)

    # 3) Layout
    return _multipartite_positions(graph, align=align)

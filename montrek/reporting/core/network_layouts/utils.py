import networkx as nx
from reporting.core.network_layouts.typing import Pos
from reporting.core.reporting_data import ReportingNetworkData


def layered_pos(reporting_data: ReportingNetworkData, align: str = "horizontal") -> Pos:
    """
    Pure-Python layered positions:
      - align='horizontal' -> ranks stacked top→bottom (TB)
      - align='vertical'   -> ranks side-by-side left→right (LR)
    """
    graph = reporting_data.graph
    # Layer nodes by topological generations (works best for DAGs)
    if nx.is_directed_acyclic_graph(graph):
        layers = {
            n: i for i, gen in enumerate(nx.topological_generations(graph)) for n in gen
        }
    else:
        # Fallback: BFS layering from zero-in-degree nodes (or arbitrary root)
        roots = [n for n in graph if graph.in_degree(n) == 0] or [
            next(iter(graph.nodes))
        ]
        layers = {r: 0 for r in roots}
        from collections import deque

        dq = deque(roots)
        while dq:
            u = dq.popleft()
            for v in graph.successors(u):
                if v not in layers:
                    layers[v] = layers[u] + 1
                    dq.append(v)
        for n in graph:  # any isolated nodes
            layers.setdefault(n, 0)

    nx.set_node_attributes(graph, layers, "subset")
    if reporting_data.group_attr:
        subsets = {}
        for n, layer in layers.items():
            group = graph.nodes[n].get(reporting_data.group_attr, 0)
            # multipartite_layout sorts subsets uniquely; we combine into tuple
            subsets[n] = (layer, group)

        nx.set_node_attributes(graph, subsets, "subset")

    # --- Step 3: layout ---
    return nx.multipartite_layout(graph, subset_key="subset", align=align, scale=1.0)

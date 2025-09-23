import networkx as nx
from reporting.core.network_layouts.typing import Pos


def layered_pos(G: nx.DiGraph, align: str = "horizontal") -> Pos:
    """
    Pure-Python layered positions:
      - align='horizontal' -> ranks stacked top→bottom (TB)
      - align='vertical'   -> ranks side-by-side left→right (LR)
    """
    # Layer nodes by topological generations (works best for DAGs)
    if nx.is_directed_acyclic_graph(G):
        layers = {
            n: i for i, gen in enumerate(nx.topological_generations(G)) for n in gen
        }
    else:
        # Fallback: BFS layering from zero-in-degree nodes (or arbitrary root)
        roots = [n for n in G if G.in_degree(n) == 0] or [next(iter(G.nodes))]
        layers = {r: 0 for r in roots}
        from collections import deque

        dq = deque(roots)
        while dq:
            u = dq.popleft()
            for v in G.successors(u):
                if v not in layers:
                    layers[v] = layers[u] + 1
                    dq.append(v)
        for n in G:  # any isolated nodes
            layers.setdefault(n, 0)

    nx.set_node_attributes(G, layers, "subset")
    return nx.multipartite_layout(G, subset_key="subset", align=align, scale=1.0)

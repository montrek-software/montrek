import itertools
import math
from typing import Any

import networkx as nx
import numpy as np
from plotly.graph_objs import Scatter
from reporting.core.reporting_colors import Color, ReportingColors
from reporting.core.reporting_data import ReportingNetworkData
from reporting.core.reporting_plots import ReportingPlotBase


class ReportingNetworkPlot(ReportingPlotBase[ReportingNetworkData]):
    def _check_reporting_data(self, reporting_data: ReportingNetworkData):
        return

    def _get_figure_data(
        self, _x: list[Any], reporting_data: ReportingNetworkData
    ) -> list[Scatter]:
        graph = reporting_data.graph
        pos = self.grouped_grid_layout(reporting_data)
        edge_trace = self.get_edges(pos, graph)
        node_trace = self.get_nodes(pos, reporting_data)
        return [edge_trace, node_trace]

    def grouped_grid_layout(
        self,
        reporting_data: ReportingNetworkData,
        n_cols: int | None = None,
        cell_w: float = 10.0,
        cell_h: float = 8.0,
        pad: float = 1.0,
        sublayout: str = "spring",  # "spring" | "kamada_kawai" | "circular"
        seed: int = 42,
    ) -> dict[str, np.ndarray]:
        """
        Place nodes in a grid of cells by `group_attr`. Each group's subgraph is
        laid out inside its own cell, normalized to fit with padding.

        - No overlap between different groups (each group stays in its cell).
        - Within a group, nodes can still overlap if there are many; increase cell_w/h.

        Returns:
            dict[node] -> np.array([x, y])
        """
        graph = reporting_data.graph
        group_attr = reporting_data.group_attr
        # --- 1) group nodes ---
        groups: dict[str, list[str]] = {}
        for node, attrs in graph.nodes(data=True):
            groups.setdefault(attrs.get(group_attr, "default"), []).append(node)

        group_items = sorted(groups.items(), key=lambda kv: kv[0])  # stable ordering
        n_groups = len(group_items)

        # --- 2) decide grid size ---
        if n_cols is None:
            n_cols = math.ceil(math.sqrt(n_groups))

        # --- 3) choose sublayout fn ---
        def _sublayout(gsub, _seed):
            if len(gsub) == 1:
                # single node at center
                lone = next(iter(gsub.nodes()))
                return {lone: np.array([0.5, 0.5])}
            if sublayout == "spring":
                return nx.spring_layout(gsub, seed=_seed, dim=2)
            if sublayout == "kamada_kawai":
                return nx.kamada_kawai_layout(gsub, dim=2)
            if sublayout == "circular":
                return nx.circular_layout(gsub, dim=2)
            return nx.spring_layout(gsub, seed=_seed, dim=2)

        pos: dict = {}

        # --- 4) layout each group in its own cell ---
        for i, (group_name, nodes) in enumerate(group_items):
            gsub = graph.subgraph(nodes)

            # local layout in [arbitrary coordinates]
            sub_pos = _sublayout(gsub, seed + i)

            # normalize to [0,1]x[0,1] to avoid overlaps across groups
            xs = np.array([xy[0] for xy in sub_pos.values()], dtype=float)
            ys = np.array([xy[1] for xy in sub_pos.values()], dtype=float)

            # handle degenerate ranges (e.g., 2 nodes perfectly aligned)
            x_min, x_max = float(xs.min()), float(xs.max())
            y_min, y_max = float(ys.min()), float(ys.max())
            x_range = x_max - x_min if x_max > x_min else 1.0
            y_range = y_max - y_min if y_max > y_min else 1.0

            # normalize to [0,1]
            for n in sub_pos:
                x, y = sub_pos[n]
                sub_pos[n] = np.array([(x - x_min) / x_range, (y - y_min) / y_range])

            # scale to cell with padding
            inner_w = max(cell_w - 2 * pad, 0.1)
            inner_h = max(cell_h - 2 * pad, 0.1)

            # cell origin (top-left of its cell)
            row = i // n_cols
            col = i % n_cols
            cell_origin = np.array([col * cell_w, row * cell_h])

            for n, (ux, uy) in sub_pos.items():
                # place inside padded inner box
                x = cell_origin[0] + pad + ux * inner_w
                y = cell_origin[1] + pad + uy * inner_h
                pos[n] = np.array([x, y])

        return pos

    def get_edges(self, pos: dict[str, np.ndarray], graph: nx.DiGraph) -> Scatter:
        edge_x, edge_y = [], []
        for src, dst in graph.edges():
            x0, y0 = pos[src]
            x1, y1 = pos[dst]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        return Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=1, color="#888"),
            mode="lines",
            hoverinfo="none",
        )

    def get_nodes(
        self, pos: dict[str, np.ndarray], reporting_data: ReportingNetworkData
    ) -> Scatter:
        graph = reporting_data.graph
        group_color_map = self.get_group_color_map(reporting_data.group_attr, graph)
        node_x, node_y, node_text, node_symbols, node_colors = (
            [],
            [],
            [],
            [],
            [],
        )
        for node, attrs in graph.nodes(data=True):
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"<b>{node}</b>")
            if reporting_data.symbol_attr:
                node_symbols.append(
                    reporting_data.symbol_map.get(
                        attrs.get(reporting_data.symbol_attr), "circle"
                    )
                )
            group = attrs.get(reporting_data.group_attr)
            node_colors.append(group_color_map.get(group, "gray"))
        marker_attrs = {
            "size": reporting_data.marker_size,
            "line_width": reporting_data.marker_line_width,
            "color": node_colors,
        }
        if reporting_data.symbol_attr:
            marker_attrs["symbol"] = node_symbols
        return Scatter(
            x=node_x, y=node_y, mode="markers+text", text=node_text, marker=marker_attrs
        )

    def get_group_color_map(
        self, group: str | None, graph: nx.DiGraph
    ) -> dict[Any, Color]:
        if not group:
            return {}

        groups = list({attrs.get(group) for _, attrs in graph.nodes(data=True)})
        color_palette = ReportingColors().hex_color_palette()
        color_cycle = itertools.cycle(color_palette)
        return {gr: next(color_cycle) for gr in groups}

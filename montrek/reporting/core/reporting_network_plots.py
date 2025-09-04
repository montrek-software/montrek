from typing import Any

import networkx as nx
import numpy as np
from plotly.graph_objs import Scatter
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
        self, reporting_data: ReportingNetworkData
    ) -> dict[str, np.ndarray]:
        graph = reporting_data.graph
        if graph.number_of_nodes() == 0:
            return {}
        return nx.spring_layout(graph, seed=42, dim=2)

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
        node_x, node_y, node_text, node_symbols = (
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
        marker_attrs = {
            "size": reporting_data.marker_size,
            "line_width": reporting_data.marker_line_width,
        }
        if reporting_data.symbol_attr:
            marker_attrs["symbol"] = node_symbols
        return Scatter(
            x=node_x, y=node_y, mode="markers+text", text=node_text, marker=marker_attrs
        )

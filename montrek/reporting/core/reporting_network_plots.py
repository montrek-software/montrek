import itertools
from typing import Any

import networkx as nx
import numpy as np
from plotly.graph_objs import Scatter
from reporting.core.network_layouts.layouts import NetworkLayoutsFactory
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
        layout = reporting_data.layout
        pos = self.get_pos(layout, graph, reporting_data)
        edge_trace = self.get_edges(pos, graph)
        node_trace = self.get_nodes(pos, reporting_data)
        return [edge_trace, node_trace]

    def update_axis_layout(self, reporting_data: ReportingNetworkData):
        self.figure.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=reporting_data.fig_height,
            showlegend=False,
        )
        self.figure.update_xaxes(automargin=True)
        self.figure.update_yaxes(automargin=True)

    def get_pos(self, layout: str, reporting_data: ReportingNetworkData):
        return NetworkLayoutsFactory.get(layout).pos(reporting_data)

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
        (
            node_x,
            node_y,
            node_text,
            node_symbols,
            node_colors,
            node_urls,
            node_hovertexts,
        ) = (
            [],
            [],
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
            node_urls.append(attrs.get(reporting_data.link_attr))
            node_hovertexts.append(attrs.get(reporting_data.hover_attr, ""))
        marker_attrs = {
            "size": reporting_data.marker_size,
            "line_width": reporting_data.marker_line_width,
            "color": node_colors,
        }
        if reporting_data.symbol_attr:
            marker_attrs["symbol"] = node_symbols
        return Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=node_text,
            marker=marker_attrs,
            name="nodes",
            customdata=node_urls,  # ← attach URLs here
            hovertext=node_hovertexts,
            hoverinfo="text",
            hovertemplate="%{text}<br>%{hovertext}<extra></extra>",
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

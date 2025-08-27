import itertools
import math

import networkx as nx
import numpy as np
import plotly.graph_objects as go
from baseclasses.models import (
    HubValueDate,
    MontrekHubABC,
    MontrekLinkABC,
    MontrekSatelliteABC,
    MontrekTimeSeriesSatelliteABC,
)
from django.apps import apps
from django.db.models.fields.related import ForwardManyToOneDescriptor
from info.dataclasses.db_structure_container import (
    DbStructureContainer,
    DbStructureHub,
    DbStructureHubValueDate,
    DbStructureLink,
    DbStructureSatellite,
    DbStructureTSSatellite,
)
from reporting.core.reporting_colors import ReportingColors
from reporting.managers.montrek_report_manager import MontrekReportManager


class InfoDbStructureManager:
    def get_db_structure_container(self) -> dict[str, DbStructureContainer]:
        all_models = apps.get_models()
        container_dict = {}
        excluded_apps = ["montrek_example", "baseclasses", "info"]
        for model in all_models:
            app = model._meta.app_label
            if app in excluded_apps:
                continue
            model_name = model.__name__
            db_table_name = model._meta.db_table
            if app not in container_dict:
                container_dict[app] = DbStructureContainer()
            model_inst = model()
            structure_kwargs = {
                "model_name": model_name,
                "db_table_name": db_table_name,
                "app": app,
            }
            if isinstance(model_inst, MontrekHubABC):
                container_dict[app].hubs.append(DbStructureHub(**structure_kwargs))
            elif isinstance(model_inst, HubValueDate):
                hub = self._get_related_field_name(model.hub)
                container_dict[app].hub_value_dates.append(
                    DbStructureHubValueDate(**structure_kwargs, hub=hub)
                )
            elif isinstance(model_inst, MontrekSatelliteABC):
                hub = self._get_related_field_name(model.hub_entity)
                container_dict[app].sats.append(
                    DbStructureSatellite(**structure_kwargs, hub=hub)
                )
            elif isinstance(model_inst, MontrekTimeSeriesSatelliteABC):
                hub_value_date = self._get_related_field_name(model.hub_value_date)
                container_dict[app].ts_sats.append(
                    DbStructureTSSatellite(
                        **structure_kwargs, hub_value_date=hub_value_date
                    )
                )
            elif isinstance(model_inst, MontrekLinkABC):
                hub_in = self._get_related_field_name(model.hub_in)
                hub_out = self._get_related_field_name(model.hub_out)
                container_dict[app].links.append(
                    DbStructureLink(**structure_kwargs, hub_in=hub_in, hub_out=hub_out)
                )

        return container_dict

    def to_plotly_figure(self, graph: nx.DiGraph) -> go.Figure:
        """
        Convert a networkx DiGraph into an interactive Plotly figure.
        """
        # pos = nx.spring_layout(graph, seed=42)
        pos = self.grouped_grid_layout(graph)

        # edges
        edge_x, edge_y = [], []
        for src, dst in graph.edges():
            x0, y0 = pos[src]
            x1, y1 = pos[dst]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=1, color="#888"),
            mode="lines",
            hoverinfo="none",
        )

        # assign colors by app
        apps = list({attrs.get("app") for _, attrs in graph.nodes(data=True)})
        color_palette = ReportingColors().hex_color_palette()
        color_cycle = itertools.cycle(color_palette)
        app_colors = {app: next(color_cycle) for app in apps}
        symbol_map = {
            "hub": "square",
            "hub_value_date": "square",
            "satellite": "circle",
            "time_series_satellite": "circle",
            "link": "diamond",
        }

        node_x, node_y, node_text, hover_text, node_color, node_symbols = (
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
            txt = (
                node.replace("Satellite", "")
                .replace("Link", "")
                .replace("Hub", "")
                .replace("ValueDate", "")
            )
            node_text.append(f"<b>{txt}</b>")
            t = attrs.get("type")
            hover_text.append(f"<b>{node}</b><br>{t}<br>app={attrs.get('app')}")
            node_symbols.append(symbol_map.get(t, "circle"))
            node_color.append(app_colors.get(attrs.get("app"), "gray"))

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=node_text,
            # textposition="top center",
            hovertext=hover_text,
            hoverinfo="text",
            marker=dict(color=node_color, size=20, line_width=2, symbol=node_symbols),
        )

        return go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                hovermode="closest",
                margin=dict(b=0, l=0, r=0, t=0),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            ),
        )

    def grouped_grid_layout(
        self,
        graph: nx.Graph,
        group_attr: str = "app",
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
        # --- 1) group nodes ---
        groups: dict[str, list[str]] = {}
        for node, attrs in graph.nodes(data=True):
            groups.setdefault(attrs.get(group_attr, "default"), []).append(node)

        group_items = sorted(groups.items(), key=lambda kv: kv[0])  # stable ordering
        n_groups = len(group_items)

        # --- 2) decide grid size ---
        if n_cols is None:
            n_cols = math.ceil(math.sqrt(n_groups))
        n_rows = math.ceil(n_groups / n_cols)

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

    def grouped_layout(self, graph, group_attr="app", seed=42):
        # Group nodes by app
        groups = {}
        for node, attrs in graph.nodes(data=True):
            groups.setdefault(attrs.get(group_attr, "default"), []).append(node)

        pos = {}
        n_cols = 6

        for i, (app, nodes) in enumerate(groups.items()):
            subgraph = graph.subgraph(nodes)
            sub_pos = nx.spring_layout(subgraph, seed=seed)  # local layout
            offset_x = i % n_cols
            offset_y = i / n_cols
            offset = [offset_x + 15, offset_y + 15]
            for node, (x, y) in sub_pos.items():
                pos[node] = np.array([x, y]) + offset

        return pos

    def _get_related_field_name(self, descriptor: ForwardManyToOneDescriptor) -> str:
        return descriptor.field.remote_field.model.__name__

    def to_networkx_graph(
        self, container_dict: dict[str, DbStructureContainer]
    ) -> nx.DiGraph:
        """
        Convert the DbStructureContainer dictionary into a networkx directed graph.

        Args:
            container_dict (dict): Dictionary containing DbStructureContainer objects.

        Returns:
            nx.DiGraph: A directed graph representing the database structure.
        """
        graph = nx.DiGraph()

        for app, container in container_dict.items():
            for hub in container.hubs:
                graph.add_node(hub.model_name, type="hub", app=app)

            for hub_value_date in container.hub_value_dates:
                graph.add_node(
                    hub_value_date.model_name, type="hub_value_date", app=app
                )
                graph.add_edge(hub_value_date.hub, hub_value_date.model_name)

            for sat in container.sats:
                graph.add_node(sat.model_name, type="satellite", app=app)
                graph.add_edge(sat.hub, sat.model_name)

            for ts_sat in container.ts_sats:
                graph.add_node(ts_sat.model_name, type="time_series_satellite", app=app)
                graph.add_edge(ts_sat.hub_value_date, ts_sat.model_name)

            for link in container.links:
                graph.add_node(link.model_name, type="link", app=app)
                graph.add_edge(link.hub_in, link.model_name)
                graph.add_edge(link.model_name, link.hub_out)

        return graph

    def to_html(self):
        db_structure_container = self.get_db_structure_container()
        graph = self.to_networkx_graph(db_structure_container)
        figure = self.to_plotly_figure(graph)
        return figure.to_html(full_html=False, include_plotlyjs=False)


class InfoDbstructureReportManager(MontrekReportManager):
    def collect_report_elements(self):
        self.append_report_element(self.get_db_structure_network_plot())

    def get_db_structure_network_plot(self):
        return InfoDbStructureManager()

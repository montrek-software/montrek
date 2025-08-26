import os

import matplotlib.pyplot as plt
import networkx as nx
from baseclasses.models import (
    HubValueDate,
    MontrekHubABC,
    MontrekLinkABC,
    MontrekSatelliteABC,
    MontrekTimeSeriesSatelliteABC,
)
from django.apps import apps
from django.conf import settings
from django.db.models.fields.related import ForwardManyToOneDescriptor
from info.dataclasses.db_structure_container import (
    DbStructureContainer,
    DbStructureHub,
    DbStructureHubValueDate,
    DbStructureLink,
    DbStructureSatellite,
    DbStructureTSSatellite,
)
from reporting.core.reporting_text import ReportingImage
from reporting.managers.montrek_report_manager import MontrekReportManager


class InfoDbStructureManager:
    def get_db_structure_container(self) -> dict[str, DbStructureContainer]:
        all_models = apps.get_models()
        container_dict = {}
        for model in all_models:
            app = model._meta.app_label
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

    def save_graph_as_png(
        self, graph: nx.DiGraph, filename: str = "db_structure.png"
    ) -> str:
        """
        Save the networkx graph as a PNG file.

        Args:
            graph (nx.DiGraph): The directed graph to save.
            filename (str): The name of the file to save the graph as.
        Returns: path to image
        """
        path = os.path.join(settings.MEDIA_ROOT, filename)
        plt.figure(figsize=(24, 12))
        pos = nx.spring_layout(graph)
        nx.draw(
            graph,
            pos,
            with_labels=True,
            node_size=3000,
            node_color="lightblue",
            font_size=10,
            font_weight="bold",
            arrowsize=20,
        )
        plt.savefig(path)
        plt.close()
        return path

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


class InfoDbstructureReportManager(MontrekReportManager):
    def collect_report_elements(self):
        self.append_report_element(self.get_db_structure_network_plot())

    def get_db_structure_network_plot(self):
        db_structure_manager = InfoDbStructureManager()
        db_structure_container = db_structure_manager.get_db_structure_container()
        graph = db_structure_manager.to_networkx_graph(db_structure_container)
        image_path = db_structure_manager.save_graph_as_png(graph)
        return ReportingImage(settings.MEDIA_URL + image_path)

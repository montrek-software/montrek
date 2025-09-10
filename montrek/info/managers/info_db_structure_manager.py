import networkx as nx
import pandas as pd
from baseclasses.models import (
    HubValueDate,
    MontrekHubABC,
    MontrekLinkABC,
    MontrekSatelliteABC,
    MontrekTimeSeriesSatelliteABC,
)
from baseclasses.typing import TableElementsType
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
from reporting.core.reporting_data import ReportingNetworkData
from reporting.core.reporting_network_plots import ReportingNetworkPlot
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_report_manager import MontrekReportManager
from reporting.managers.montrek_table_manager import MontrekDataFrameTableManager


class InfoDbStructureManager:
    def get_db_structure_container(self) -> dict[str, DbStructureContainer]:
        all_models = apps.get_models()
        container_dict = {}
        excluded_apps = ["montrek_example", "baseclasses"]
        included_apps = ["fund", "general_partner", "prompt"]
        for model in all_models:
            app = model._meta.app_label
            if app in excluded_apps:
                continue
            if app not in included_apps:
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
                hub_db = self._get_related_db_name(model.hub)
                container_dict[app].hub_value_dates.append(
                    DbStructureHubValueDate(**structure_kwargs, hub=hub, hub_db=hub_db)
                )
            elif isinstance(model_inst, MontrekSatelliteABC):
                hub = self._get_related_field_name(model.hub_entity)
                hub_db = self._get_related_db_name(model.hub_entity)
                container_dict[app].sats.append(
                    DbStructureSatellite(**structure_kwargs, hub=hub, hub_db=hub_db)
                )
            elif isinstance(model_inst, MontrekTimeSeriesSatelliteABC):
                hub_value_date = self._get_related_field_name(model.hub_value_date)
                hub_value_date_db = self._get_related_db_name(model.hub_value_date)
                container_dict[app].ts_sats.append(
                    DbStructureTSSatellite(
                        **structure_kwargs,
                        hub_value_date=hub_value_date,
                        hub_value_date_db=hub_value_date_db,
                    )
                )
            elif isinstance(model_inst, MontrekLinkABC):
                hub_in = self._get_related_field_name(model.hub_in)
                hub_out = self._get_related_field_name(model.hub_out)
                hub_in_db = self._get_related_db_name(model.hub_in)
                hub_out_db = self._get_related_db_name(model.hub_out)
                container_dict[app].links.append(
                    DbStructureLink(
                        **structure_kwargs,
                        hub_in=hub_in,
                        hub_out=hub_out,
                        hub_in_db=hub_in_db,
                        hub_out_db=hub_out_db,
                    )
                )

        return container_dict

    def get_db_structure_df(
        self, container: dict[str, DbStructureContainer]
    ) -> pd.DataFrame:
        df_data = {"app": [], "type": [], "name": [], "db_table_name": [], "link": []}
        for app in container.keys():
            for hub in container[app].hubs:
                df_data["app"].append(app)
                df_data["name"].append(hub.model_name)
                df_data["db_table_name"].append(hub.db_table_name)
                df_data["type"].append("Hub")
                df_data["link"].append("")
            for hub_vd in container[app].hub_value_dates:
                df_data["app"].append(app)
                df_data["name"].append(hub_vd.model_name)
                df_data["db_table_name"].append(hub_vd.db_table_name)
                df_data["type"].append("HubValueDate")
                df_data["link"].append(f"Hub: {hub_vd.hub}")
            for sat in container[app].sats:
                df_data["app"].append(app)
                df_data["name"].append(sat.model_name)
                df_data["db_table_name"].append(sat.db_table_name)
                df_data["type"].append("Satellite")
                df_data["link"].append(f"Hub: {sat.hub}")
            for sat in container[app].ts_sats:
                df_data["app"].append(app)
                df_data["name"].append(sat.model_name)
                df_data["db_table_name"].append(sat.db_table_name)
                df_data["type"].append("TS Satellite")
                df_data["link"].append(f"Hub Value Date: {sat.hub_value_date}")
            for link in container[app].links:
                df_data["app"].append(app)
                df_data["name"].append(link.model_name)
                df_data["db_table_name"].append(link.db_table_name)
                df_data["type"].append("Link")
                df_data["link"].append(
                    f"Hub in: {link.hub_in}, Hub out: {link.hub_out}"
                )
        return pd.DataFrame(df_data)

    def get_db_structure_description(
        self, container: dict[str, DbStructureContainer]
    ) -> str:
        description_str = ""
        for app in container.keys():
            for hub in container[app].hubs:
                description_str += str(hub)
            for hub_vd in container[app].hub_value_dates:
                description_str += str(hub_vd)
            for sat in container[app].sats:
                description_str += str(sat)
            for sat in container[app].ts_sats:
                description_str += str(sat)
            for link in container[app].links:
                description_str += str(link)
        return description_str

    def _get_related_field_name(self, descriptor: ForwardManyToOneDescriptor) -> str:
        return descriptor.field.remote_field.model.__name__

    def _get_related_db_name(self, descriptor: ForwardManyToOneDescriptor) -> str:
        return descriptor.field.remote_field.model._meta.db_table


class InfoDbStructureNetworkReportingElement:
    def __init__(self, db_structure_container):
        self.db_structure_container = db_structure_container

    def to_networkx_graph(self) -> nx.DiGraph:
        """
        Convert the DbStructureContainer dictionary into a networkx directed graph.

        Args:
            container_dict (dict): Dictionary containing DbStructureContainer objects.

        Returns:
            nx.DiGraph: A directed graph representing the database structure.
        """
        graph = nx.DiGraph()

        for app, container in self.db_structure_container.items():
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


class InfoDbStructureDataFrameTableManager(MontrekDataFrameTableManager):
    @property
    def table_elements(self) -> TableElementsType:
        return [
            te.StringTableElement("App", "app"),
            te.StringTableElement("Type", "type"),
            te.StringTableElement("Name", "name"),
            te.StringTableElement("DB Name", "db_table_name"),
            te.StringTableElement("Link", "link"),
        ]


class InfoDbstructureReportManager(MontrekReportManager):
    def collect_report_elements(self):
        self.db_structure_manager = InfoDbStructureManager()
        self.append_report_element(self.get_db_structure_network_plot())
        self.append_report_element(self.get_db_structure_table())

    def get_db_structure_network_plot(self):
        db_structure_container = self.db_structure_manager.get_db_structure_container()
        nw_ele = InfoDbStructureNetworkReportingElement(db_structure_container)
        graph = nw_ele.to_networkx_graph()
        symbol_map = {
            "hub": "square",
            "hub_value_date": "square",
            "satellite": "circle",
            "time_series_satellite": "circle",
            "link": "diamond",
        }
        reporting_data = ReportingNetworkData(
            title="DB Structure",
            graph=graph,
            symbol_attr="type",
            symbol_map=symbol_map,
            group_attr="app",
            fig_height=1000,
        )
        report_ele = ReportingNetworkPlot()
        report_ele.generate(reporting_data)
        return report_ele

    def get_db_structure_table(self):
        db_structure_container = self.db_structure_manager.get_db_structure_container()
        db_structure_df = self.db_structure_manager.get_db_structure_df(
            db_structure_container
        )
        return InfoDbStructureDataFrameTableManager(
            {"df_data": db_structure_df.to_dict(orient="records")}
        )

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
                container_dict[app].sats.append(
                    DbStructureSatellite(**structure_kwargs)
                )
            elif isinstance(model_inst, MontrekTimeSeriesSatelliteABC):
                hub_value_date = self._get_related_field_name(model.hub_value_date)
                container_dict[app].ts_sats.append(
                    DbStructureTSSatellite(
                        **structure_kwargs, hub_value_date=hub_value_date
                    )
                )
            elif isinstance(model_inst, MontrekLinkABC):
                container_dict[app].links.append(DbStructureLink(**structure_kwargs))

        return container_dict

    def _get_related_field_name(self, descriptor: ForwardManyToOneDescriptor) -> str:
        return descriptor.field.remote_field.model.__name__

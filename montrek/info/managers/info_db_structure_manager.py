from baseclasses.models import MontrekHubABC
from django.apps import apps
from info.dataclasses.db_structure_container import DbStructureContainer, DbStructureHub


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
            if isinstance(model(), MontrekHubABC):
                container_dict[app].hubs.append(
                    DbStructureHub(
                        model_name=model_name, db_table_name=db_table_name, app=app
                    )
                )

        return container_dict

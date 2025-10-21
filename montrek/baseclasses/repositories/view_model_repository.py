import datetime
import logging
from copy import deepcopy
from typing import Any

from baseclasses.models import MontrekHubABC, MontrekSatelliteBaseABC
from baseclasses.repositories.db.db_staller import DbStaller
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class ViewModelRepository:
    def __init__(self, view_model: None | type[models.Model]):
        self.view_model = view_model

    def has_view_model(self) -> bool:
        return self.view_model is not None

    @classmethod
    def generate_view_model(
        cls,
        module_name: str,
        repository_name: str,
        hub_class: type[MontrekHubABC],
        fields: dict[str, Any],
    ) -> type[models.Model]:
        class Meta:
            # Only works if repository is in repositories folder
            app_label = module_name.split(".repositories")[0].split(".")[-1]
            managed = True
            db_table = f"{app_label}_{repository_name.lower()}_view_model"

        for key, field in fields.items():
            field = deepcopy(field)
            field.null = True
            field.blank = True
            field.name = key
            fields[key] = field

        fields["value_date_list_id"] = models.IntegerField(null=True, blank=True)
        fields["hub"] = models.ForeignKey(hub_class, on_delete=models.CASCADE)

        attrs = {
            "__module__": repository_name,
            "Meta": Meta,
            "reference_date": datetime.date.today(),
        }
        attrs.update(fields)
        model_name = repository_name + "ViewModel"
        model = type(model_name, (models.Model,), attrs)
        return model

    def store_in_view_model(
        self,
        db_staller: DbStaller | None,
        query: models.QuerySet,
        hub_class: type[MontrekHubABC],
        fields: list[str],
    ):
        if not self.view_model:
            return

        def sat_hub_pk(sat: MontrekSatelliteBaseABC) -> int:
            if sat.is_timeseries:
                return sat.hub_value_date.hub.pk
            else:
                return sat.hub_entity_id

        if db_staller is not None:
            new_hub_ids = [hub.pk for hub in db_staller.get_hubs()[hub_class]]
            new_sats_dict = db_staller.get_new_satellites()
            for sat_class in new_sats_dict:
                new_hub_ids += [sat_hub_pk(sat) for sat in new_sats_dict[sat_class]]

            query_create = query.filter(hub_entity_id__in=new_hub_ids)
            self.store_query_in_view_model(query_create, fields, "create")
            delete_hubs = [hub for hub in db_staller.get_updated_hubs()[hub_class]]
            for delete_hub in delete_hubs:
                self.delete_from_view_model(delete_hub)
            updated_hub_ids = []
            updated_sats_dict = db_staller.get_updated_satellites()
            for sat_class in updated_sats_dict:
                updated_hub_ids += [
                    sat_hub_pk(sat) for sat in updated_sats_dict[sat_class]
                ]

            def add_link_hub(link_class, db_staller_links):
                hub_in_model = link_class.hub_in.field.related_model
                if hub_in_model == hub_class:
                    hub_tag = "hub_in"
                else:
                    hub_tag = "hub_out"
                hub_ids = []
                for link in db_staller_links[link_class]:
                    hub_ids.append(getattr(link, hub_tag).pk)
                return hub_ids

            for link_class in db_staller.links:
                updated_hub_ids += add_link_hub(link_class, db_staller.links)
            for link_class in db_staller.updated_links:
                updated_hub_ids += add_link_hub(link_class, db_staller.updated_links)
            query_update = query.filter(hub_entity_id__in=updated_hub_ids)
            self.store_query_in_view_model(query_update, fields, "update")
            return
        self.store_query_in_view_model(query, fields)

    def store_query_in_view_model(
        self, query: models.QuerySet, fields: list[str], mode: str = "all"
    ):
        self._debug_logging("Start store_query_in_view_model")
        data = list(query.values())
        for row in data:
            if row["value_date"]:
                row["value_date"] = timezone.make_aware(
                    datetime.datetime.combine(row["value_date"], datetime.time()),
                    timezone.get_current_timezone(),
                )
        instances = [self.view_model(**item) for item in data]
        if mode == "all":
            self.view_model.objects.all().delete()
            self.view_model.objects.bulk_create(instances, batch_size=1000)
        elif mode == "create":
            if instances:
                self.view_model.objects.filter(
                    hub_entity_id__in=[inst.hub_entity_id for inst in instances]
                ).delete()
            self.view_model.objects.bulk_create(
                instances,
                batch_size=1000,
            )

        elif mode == "update":
            self.view_model.objects.bulk_update(
                instances, batch_size=1000, fields=fields
            )
        self._debug_logging("End store_query_in_view_model")

    def delete_from_view_model(self, obj: MontrekHubABC):
        if not self.view_model:
            return
        deleted_object = self.view_model.objects.filter(hub_entity_id=obj.pk)
        deleted_object.delete()

    def _debug_logging(self, msg: str):
        logger.debug("%s: %s", self.__class__.__name__, msg)

import datetime
import logging
import time
from copy import deepcopy
from typing import Any

from baseclasses.models import MontrekHubABC, MontrekSatelliteBaseABC
from baseclasses.repositories.db.db_staller import DbStaller
from django.db import models, transaction
from django.db.utils import IntegrityError
from django.utils import timezone
from psycopg2.errors import UniqueViolation

logger = logging.getLogger(__name__)


class ViewModelRepository:
    MAX_RETRIES = 3

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

    # ───────────────────────────────────────────────
    # Public API
    # ───────────────────────────────────────────────
    def store_in_view_model(
        self,
        db_staller: "DbStaller | None",
        query: models.QuerySet,
        hub_class: type["MontrekHubABC"],
    ):
        """Store query results into the view model, handling create/update/delete logic."""
        if not self.view_model:
            return

        if db_staller is None:
            # No staging updates: store everything
            self.store_query_in_view_model(query)
            return

        # Create operations
        new_hub_ids = self._collect_new_hub_ids(db_staller, hub_class)
        query_create = query.filter(hub_entity_id__in=new_hub_ids)
        self.store_query_in_view_model(query_create, "create")

        # Delete operations
        self._delete_updated_hubs(db_staller, hub_class)

        # Update operations
        updated_hub_ids = self._collect_updated_hub_ids(db_staller, hub_class)
        query_update = query.filter(hub_entity_id__in=updated_hub_ids)
        self.store_query_in_view_model(query_update, "update")

    # ───────────────────────────────────────────────
    # Private helpers
    # ───────────────────────────────────────────────
    def _sat_hub_pk(self, sat: "MontrekSatelliteBaseABC") -> int:
        """Extract the hub primary key from a satellite instance."""
        return sat.hub_value_date.hub.pk if sat.is_timeseries else sat.hub_entity_id

    def _collect_new_hub_ids(
        self, db_staller: "DbStaller", hub_class: type["MontrekHubABC"]
    ) -> list[int]:
        """Gather hub IDs that are newly created or belong to new satellites."""
        hub_ids = [hub.pk for hub in db_staller.get_hubs().get(hub_class, [])]

        for satellites in db_staller.get_new_satellites().values():
            hub_ids += [self._sat_hub_pk(sat) for sat in satellites]
        return hub_ids

    def _delete_updated_hubs(
        self, db_staller: "DbStaller", hub_class: type["MontrekHubABC"]
    ):
        """Delete view model records corresponding to updated hubs."""
        updated_hubs = db_staller.get_updated_hubs().get(hub_class, [])
        for hub in updated_hubs:
            self.delete_from_view_model(hub)

    def _collect_updated_hub_ids(
        self, db_staller: "DbStaller", hub_class: type["MontrekHubABC"]
    ) -> list[int]:
        """Collect hub IDs that are updated via satellites or links."""
        hub_ids = []

        # Satellites
        for sat_class, satellites in db_staller.get_updated_satellites().items():
            hub_ids += [self._sat_hub_pk(sat) for sat in satellites]

        # Links (both existing and updated)
        for link_source in [db_staller.links, db_staller.updated_links]:
            for link_class, link_objs in link_source.items():
                hub_ids += self._collect_link_hub_ids(link_class, link_objs, hub_class)

        return hub_ids

    def _collect_link_hub_ids(
        self,
        link_class: type[models.Model],
        link_instances: list[models.Model],
        hub_class: type["MontrekHubABC"],
    ) -> list[int]:
        """Extract hub primary keys from a link class for the relevant hub_class."""
        # Determine whether the link’s `hub_in` or `hub_out` relates to the given hub_class
        hub_in_model = link_class.hub_in.field.related_model
        hub_field = "hub_in" if hub_in_model == hub_class else "hub_out"

        return [getattr(link, hub_field).pk for link in link_instances]

    def store_query_in_view_model(self, query: models.QuerySet, mode: str = "all"):
        self._debug_logging("Start store_query_in_view_model")
        for attempt in range(self.MAX_RETRIES):
            try:
                with transaction.atomic():
                    self._try_store_query_in_view_model(query, mode)
                break
            except (IntegrityError, UniqueViolation):
                if attempt == self.MAX_RETRIES - 1:
                    raise ValueError(
                        "Maximum number of retries exceeded when storing to the view model due to repeated integrity errors."
                    )
                time.sleep(0.1)  # brief backoff

    def _try_store_query_in_view_model(self, query: models.QuerySet, mode: str = "all"):
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
        elif mode == "create" or mode == "update":
            if instances:
                self.view_model.objects.filter(
                    pk__in=[inst.pk for inst in instances]
                ).delete()
            self.view_model.objects.bulk_create(
                instances,
                batch_size=1000,
            )
        self._debug_logging("End store_query_in_view_model")

    def delete_from_view_model(self, obj: MontrekHubABC):
        if not self.view_model:
            return
        deleted_object = self.view_model.objects.filter(hub_entity_id=obj.pk)
        deleted_object.delete()

    def _debug_logging(self, msg: str):
        logger.debug("%s: %s", self.__class__.__name__, msg)

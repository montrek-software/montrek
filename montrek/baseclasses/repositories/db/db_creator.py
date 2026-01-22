import datetime
import json
import logging

import pandas as pd
from baseclasses.errors.montrek_user_error import MontrekError
from baseclasses.models import (
    HubValueDate,
    MontrekHubABC,
    MontrekLinkABC,
    MontrekOneToOneLinkABC,
    MontrekSatelliteABC,
    ValueDateList,
)
from baseclasses.repositories.db.db_creator_cache import DbCreatorCache
from baseclasses.repositories.db.db_staller import DbStaller
from baseclasses.repositories.db.satellite_creator import SatelliteCreator
from baseclasses.repositories.db.typing import DataDict, SatelliteDict
from django.db.models import JSONField, Q, QuerySet
from django.utils import timezone

logger = logging.getLogger(__name__)


class DbCreator:
    def __init__(self, db_staller: DbStaller, user_id: int):
        self.db_staller = db_staller
        self.data: DataDict = {}
        self.user_id = user_id
        self.hub: MontrekHubABC | None = None
        self.hub_value_date: HubValueDate | None = None
        self.value_date_list: ValueDateList | None = None
        self.creation_date = db_staller.creation_date
        self.new_satellites: SatelliteDict = {}
        self.existing_satellites: SatelliteDict = {}
        self.updated_satellites: SatelliteDict = {}
        self.satellite_creator = SatelliteCreator()
        self.cache: DbCreatorCache | None = None

    def create(self, data: DataDict):
        self.data = data
        self._enrich_data()
        self._get_hub_from_data()
        self._create_static_satellites()
        self._stall_hub()
        self._set_static_satellites_hub()
        self._set_value_date_list()
        self._stall_hub_value_date()
        self._create_ts_satellites()
        self._create_links()

    def _enrich_data(self):
        self.data["created_by_id"] = self.user_id
        self._upfront_formats()

    def _create_static_satellites(self):
        for sat_class in self.db_staller.get_static_satellite_classes():
            sat = self.satellite_creator.create_static_satellite(
                sat_class, self.data, self.creation_date, self.hub
            )
            if sat is None:
                continue
            self._process_static_satellite(sat)

    def _create_ts_satellites(self):
        for sat_class in self.db_staller.get_ts_satellite_classes():
            sat = self.satellite_creator.create_ts_satellite(
                sat_class, self.data, self.creation_date, self.hub_value_date
            )
            if sat is None:
                continue
            self._process_ts_satellite(sat)

    def _create_links(self):
        link_data = self._get_link_data()
        for field, values in link_data.items():
            link_class = getattr(self.hub.__class__, field).through
            values = [v for v in values if v]
            new_links = self._create_new_links(link_class, values)
            self.db_staller.stall_links(new_links)

    def _upfront_formats(self):
        for key, value in self.data.items():
            if isinstance(value, datetime.datetime):
                self._make_timezone_aware(value, key)
        for sat_class in self.db_staller.get_static_satellite_classes():
            self._convert_json(sat_class)
        if "value_date" in self.data and not pd.isnull(self.data["value_date"]):
            self.data["value_date"] = pd.to_datetime(self.data["value_date"]).date()
        if "comment" in self.data and pd.isnull(self.data["comment"]):
            self.data["comment"] = ""

    def _make_timezone_aware(self, value: datetime.datetime, key: str):
        if value.tzinfo is None:
            self.data[key] = timezone.make_aware(value, timezone.get_default_timezone())

    def _convert_json(self, sat_class: type[MontrekSatelliteABC]):
        for field in sat_class.get_value_fields():
            if field.name in self.data and isinstance(field, JSONField):
                value = self.data[field.name]
                if isinstance(value, str):
                    self.data[field.name] = json.loads(value.replace("'", '"'))

    def _process_static_satellite(self, sat: MontrekSatelliteABC):
        state_date_end_criterion = Q(hub_entity__state_date_end__gt=timezone.now())
        existing_sat = self._get_existing_satellite(sat, state_date_end_criterion)
        if existing_sat is None:
            self._stall_new_satellite(sat)
            self._close_existing_sat_if_hub_is_forced(sat)
            return
        self.hub = existing_sat.hub_entity
        self._updated_satellite(sat, existing_sat)

    def _process_ts_satellite(self, sat: MontrekSatelliteABC):
        state_date_end_criterion = Q(
            hub_value_date__hub__state_date_end__gt=timezone.now()
        )
        existing_sat = self._get_existing_satellite(sat, state_date_end_criterion)
        if existing_sat is None:
            self._stall_new_satellite(sat)
            return
        self._updated_satellite(sat, existing_sat)

    def _stall_new_satellite(self, sat: MontrekSatelliteABC):
        self.db_staller.stall_new_satellite(sat)
        sat_class = type(sat)
        self.new_satellites[sat_class] = sat

    def _stall_updated_satellite(self, sat: MontrekSatelliteABC):
        self.db_staller.stall_updated_satellite(sat)
        sat_class = type(sat)
        self.updated_satellites[sat_class] = sat

    def _set_value_date_list(self):
        value_date = self.data.get("value_date", None)
        if self.cache is not None:
            obj = self.cache.get_cached_value_date(value_date)
        else:
            obj = ValueDateList.objects.filter(value_date=value_date).first()
        if obj is None:
            obj = ValueDateList.objects.create(value_date=value_date)
            if self.cache is not None:
                self.cache.cached_value_date_lists[value_date] = obj
        self.value_date_list = obj

    def _get_hub_from_data(self):
        """
        Retrieve an existing hub entity from the database if 'hub_entity_id' is provided in self.data.
        Sets self.hub to the corresponding hub instance.
        """
        if "hub_entity_id" in self.data and not pd.isnull(self.data["hub_entity_id"]):
            hub_entity_id = self.data["hub_entity_id"]
            if self.cache is not None:
                self.hub = self.cache.get_cached_hub(hub_entity_id)
                return
            self.hub = self.db_staller.hub_class.objects.get(
                id=self.data["hub_entity_id"]
            )

    def _stall_hub(self, stall: bool = True):
        if self.hub:
            return
        self.hub = self.db_staller.hub_class(
            created_by_id=self.user_id, state_date_start=self.creation_date
        )
        if stall:
            self.db_staller.stall_hub(self.hub)

    def _stall_hub_value_date(self, stall: bool = True):
        if self.hub.id is not None:
            if self.cache is not None:
                existing_hub_value_date = self.cache.get_cached_hub_value_date(
                    self.hub.id, self.value_date_list.value_date
                )
            else:
                existing_hub_value_date = (
                    self.db_staller.hub_value_date_class.objects.filter(
                        hub=self.hub, value_date_list=self.value_date_list
                    ).first()
                )

            if existing_hub_value_date:
                self.hub_value_date = existing_hub_value_date
                return
        self.hub_value_date = self.db_staller.hub_value_date_class(
            hub=self.hub, value_date_list=self.value_date_list
        )
        if stall:
            self.db_staller.stall_hub_value_date(self.hub_value_date)

    def _set_static_satellites_hub(self):
        self._reset_hub_if_new_and_existing()
        for sat_class, sat in self.new_satellites.items():
            if sat_class.is_timeseries:
                continue
            sat.hub_entity = self.hub

    def _get_existing_satellite(
        self, sat: MontrekSatelliteABC, state_date_end_criterion: Q
    ) -> MontrekSatelliteABC | None:
        # Check if satellite already exists, if it is updated or if it is new
        sat_hash_identifier = sat.get_hash_identifier
        satellite_class = type(sat)
        if self.cache is not None:
            return self.cache.get_cached_satellite(satellite_class, sat_hash_identifier)
        return satellite_class.objects.filter(
            state_date_end_criterion,
            Q(hash_identifier=sat_hash_identifier),
            state_date_start__lte=self.creation_date,
            state_date_end__gt=self.creation_date,
        ).first()

    def _updated_satellite(
        self, sat: MontrekSatelliteABC, existing_sat: MontrekSatelliteABC
    ):
        if existing_sat.is_timeseries:
            self.hub = existing_sat.hub_value_date.hub
        else:
            self.hub = existing_sat.hub_entity
        self._raise_error_if_existing_hub_does_not_match(existing_sat)
        if existing_sat.hash_value == sat.get_hash_value:
            self.existing_satellites[existing_sat.__class__] = existing_sat
            return
        existing_sat.state_date_end = self.creation_date
        sat.state_date_start = self.creation_date
        self._stall_new_satellite(sat)
        self._stall_updated_satellite(existing_sat)

    def _reset_hub_if_new_and_existing(self):
        # if there are new and existing satellites stalled, treat every existing satellite as new
        if len(self.existing_satellites) == 0:
            return
        if len(self.new_satellites) == 0:
            return
        if any(
            sat_class in self.updated_satellites for sat_class in self.new_satellites
        ):
            return
        if "hub_entity_id" in self.data:
            return
        self.hub = None
        for existing_sat in self.existing_satellites.values():
            self._close_and_renew_satellite(existing_sat)
        self._stall_hub()

    def _close_and_renew_satellite(self, existing_sat: MontrekSatelliteABC):
        old_hub = existing_sat.hub_entity
        old_hub.state_date_end = self.db_staller.creation_date
        self.db_staller.stall_updated_hub(old_hub)
        existing_sat.state_date_end = self.db_staller.creation_date
        self.db_staller.stall_updated_satellite(existing_sat)
        existing_sat.state_date_end = self.creation_date
        existing_sat.hub_entity = None
        existing_sat.state_date_start = self.creation_date
        existing_sat.state_date_end = timezone.make_aware(
            timezone.datetime.max, timezone.get_default_timezone()
        )
        existing_sat.pk = None
        existing_sat.id = None
        self._stall_new_satellite(existing_sat)

    def _close_existing_sat_if_hub_is_forced(self, sat: MontrekSatelliteABC):
        if "hub_entity_id" not in self.data:
            return
        if self.cache is not None:
            latest_sat = self.cache.get_cached_satellite_by_hub(
                sat.__class__, self.data["hub_entity_id"]
            )
        else:
            latest_sat = (
                sat.__class__.objects.filter(hub_entity_id=self.data["hub_entity_id"])
                .order_by("-state_date_start")
                .first()
            )
        if not latest_sat:
            return

        latest_sat.state_date_end = self.creation_date
        self.db_staller.stall_updated_satellite(latest_sat)

    def _get_link_data(self) -> dict[str, list[MontrekHubABC]]:
        link_data = {}
        for key, value in self.data.items():
            if key not in self.hub._meta.get_fields():
                continue
            if isinstance(value, HubValueDate):
                link_data[key] = [value.hub]
            elif isinstance(value, MontrekHubABC):
                link_data[key] = [value]
            elif isinstance(value, list | QuerySet):
                many_links = [
                    item.hub for item in value if isinstance(item, HubValueDate)
                ]
                many_links += [
                    item for item in value if isinstance(item, MontrekHubABC)
                ]
                link_data[key] = many_links
        return link_data

    def _create_new_links(
        self, link_class: type[MontrekLinkABC], values: list[MontrekHubABC]
    ) -> list[MontrekLinkABC]:
        if link_class.hub_in.field.related_model == self.hub.__class__:
            new_links = [
                link_class(
                    hub_in=self.hub, hub_out=value, state_date_start=self.creation_date
                )
                for value in values
            ]
            return self._update_links_if_exist(new_links, "hub_in", link_class)
        new_links = [
            link_class(
                hub_in=value, hub_out=self.hub, state_date_start=self.creation_date
            )
            for value in values
        ]
        return self._update_links_if_exist(new_links, "hub_out", link_class)

    def _update_links_if_exist(
        self,
        links: list[MontrekLinkABC],
        hub_field: str,
        link_class: type[MontrekLinkABC],
    ) -> list[MontrekLinkABC]:
        if not self.hub.pk:
            return links

        is_one_to_one_link = issubclass(link_class, MontrekOneToOneLinkABC)
        if is_one_to_one_link and len(links) > 1:
            raise MontrekError(
                f"Try to link multiple items to OneToOne Link {link_class}"
            )

        # Try to get from cache first
        if self.cache is not None:
            existing_links = self.cache.get_cached_links(
                link_class, self.hub.id, hub_field
            )
        else:
            # Fallback to database query if not in cache
            filter_args = {
                f"{hub_field}": self.hub,
                "state_date_end__gt": self.creation_date,
                "state_date_start__lte": self.creation_date,
            }
            existing_links = list(link_class.objects.filter(**filter_args))

        if not existing_links:
            return links

        opposite_field = self._get_opposite_field(hub_field)
        opposite_hubs = [getattr(link, opposite_field) for link in links]
        continued_links = [
            link
            for link in existing_links
            if getattr(link, opposite_field) in opposite_hubs
        ]
        discontinued_links = [
            link
            for link in existing_links
            if getattr(link, opposite_field) not in opposite_hubs
        ]
        for link in discontinued_links:
            link.state_date_end = self.creation_date
        self.db_staller.stall_updated_links(discontinued_links)

        continued_opposite_hubs = [
            getattr(link, opposite_field) for link in continued_links
        ]
        new_links = [
            link
            for link in links
            if getattr(link, opposite_field) not in continued_opposite_hubs
        ]
        for link in new_links:
            link.state_date_start = self.creation_date
        return new_links

    def _get_opposite_field(self, field):
        return "hub_out" if field == "hub_in" else "hub_in"

    def _raise_error_if_existing_hub_does_not_match(
        self, existing_sat: MontrekSatelliteABC
    ):
        if "hub_entity_id" not in self.data:
            return
        if self.data["hub_entity_id"] != self.hub.id:
            existing_id_str = ""
            for field in existing_sat.identifier_fields:
                existing_id_str += f"{field}: {getattr(existing_sat, field)}, "
            raise MontrekError(
                f"Try to update data with ({existing_id_str}) that already exists!"
            )

    def clean(self):
        self.hub = None
        self.hub_value_date = None
        self.value_date_list = None
        self.new_satellites = {}
        self.existing_satellites = {}
        self.updated_satellites = {}


class DbBatchCreator:
    def __init__(self, db_creator: DbCreator, df: pd.DataFrame):
        self.db_creator = db_creator
        self.data_collection: list[DataDict] = []
        self.hubs: list[MontrekHubABC | None] = []
        self.df = df
        self.columns = list(df.columns)

    def fill_data_collection(self):
        for row in self.df.itertuples(index=False, name=None):
            data = dict(zip(self.columns, row, strict=False))
            # Normalize NaN → None (required for many tests)
            for key, value in data.items():
                if not isinstance(value, list | dict) and pd.isna(value):
                    data[key] = None

            self.stall_data(data)

    def stall_data(self, data: DataDict):
        self.data_collection.append(data)

    def create(self):
        logger.debug("Cache existing objects from DB")
        self.cache_data()

        logger.debug("Stall data in DbStaller")
        for data in self.data_collection:
            self.db_creator.create(data)
            self.hubs.append(self.db_creator.hub)
            self.db_creator.clean()

    def cache_data(self) -> None:
        cache = DbCreatorCache(self.db_creator.db_staller)
        cache.cache_with_data(self.data_collection)
        self.db_creator.cache = cache

import datetime
import json
import logging
from collections import defaultdict
from typing import Any, Optional, cast

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
from baseclasses.repositories.db.db_staller import DbStaller
from baseclasses.sanitizer import HtmlSanitizer
from django.db.models import JSONField, ManyToManyField, Q, QuerySet
from django.utils import timezone

type DataDict = dict[str, Any]
type SatelliteDict = dict[type[MontrekSatelliteABC], MontrekSatelliteABC]
type SatHashesMap = dict[type[MontrekSatelliteABC], str]
type SatHashesDict = dict[type[MontrekSatelliteABC], set[str]]
type HashSatMap = dict[tuple[type[MontrekSatelliteABC], str], MontrekSatelliteABC]

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
        self.sanitizer = HtmlSanitizer()
        self.cached_queryset: Optional[HashSatMap] = None
        self._cached_value_date_lists = {}
        self._cached_hub_value_dates = {}
        self._cached_hubs = {}
        self._cached_links = {}

    def create(self, data: DataDict):
        self.data = self.cleaned_data(data)
        self._enrich_data()
        self._get_hub_from_data()
        self._create_static_satellites()
        self._stall_hub()
        self._set_static_satellites_hub()
        self._set_value_date_list()
        self._stall_hub_value_date()
        self._create_ts_satellites()
        self._create_links()

    def cleaned_data(self, data: DataDict) -> DataDict:
        return {
            key: self.sanitizer.clean_html(value) if isinstance(value, str) else value
            for key, value in data.items()
        }

    def get_sat_hashes(self, data: DataDict) -> SatHashesMap:
        self.data = data
        self._get_hub_from_data()
        self._stall_hub(False)
        self._set_value_date_list()
        self._stall_hub_value_date(False)
        sat_hashes = {}
        for sat_class in self.db_staller.get_static_satellite_classes():
            sat = self._create_static_satellite(sat_class)
            if sat is None:
                continue
            sat_hashes[sat_class] = sat.get_hash_identifier

        for sat_class in self.db_staller.get_ts_satellite_classes():
            sat = self._create_ts_satellite(sat_class)
            if sat is None:
                continue
            sat_hashes[sat_class] = sat.get_hash_identifier
        self.clean()
        return sat_hashes

    def cache_hubs(self, hub_ids: set[int]):
        logger.debug("Start cache hubs")
        hubs = self.db_staller.hub_class.objects.filter(id__in=hub_ids)
        self._cached_hubs = {hub.id: hub for hub in hubs}
        logger.debug("End cache hubs")

    def cache_value_dates(self, value_dates: set[datetime.date | None]):
        logger.debug("Start cache value_dates")
        value_dates_lists = ValueDateList.objects.filter(
            Q(value_date__in=value_dates) | Q(value_date__isnull=True)
        )
        self._cached_value_date_lists = {
            value_date.value_date: value_date for value_date in value_dates_lists
        }
        logger.debug("End cache value_dates")

    def cache_hub_value_dates(
        self, hub_ids: set[int], value_dates: set[datetime.date | None]
    ):
        logger.debug("Start cache hub_value_dates")

        hub_value_dates = self.db_staller.hub_value_date_class.objects.select_related(
            "value_date_list", "hub"
        ).filter(
            Q(hub__id__in=hub_ids)
            & (
                Q(value_date_list__value_date__in=value_dates)
                | Q(value_date_list__value_date__isnull=True)
            )
        )
        self._cached_hub_value_dates = {
            (hvd.hub_id, hvd.value_date_list.value_date): hvd for hvd in hub_value_dates
        }
        logger.debug("End cache hub_value_dates")

    def cache_links(self, link_field_names: set[str]):
        """
        Cache existing links for the given hub IDs and link field names.
        Stores links in a dict keyed by (link_class, hub_id, hub_field).
        """
        logger.debug("Start cache links")

        now = timezone.now()
        cached_links = defaultdict(list)

        # Get only link classes that correspond to fields in the data
        link_classes = self._get_link_classes_for_fields(link_field_names)
        hub_ids = set(self._cached_hubs.keys())

        for link_class in link_classes:
            # Query links where hub_in or hub_out matches our hub_ids
            links = link_class.objects.select_related("hub_in", "hub_out").filter(
                Q(hub_in_id__in=hub_ids) | Q(hub_out_id__in=hub_ids),
                state_date_start__lte=now,
                state_date_end__gt=now,
            )

            for link in links:
                # Cache by hub_in
                if link.hub_in_id in hub_ids:
                    key = (link_class, link.hub_in_id, "hub_in")
                    cached_links[key].append(link)

                # Cache by hub_out
                if link.hub_out_id in hub_ids:
                    key = (link_class, link.hub_out_id, "hub_out")
                    cached_links[key].append(link)

        self._cached_links = dict(cached_links)
        logger.debug("End cache links")

    def _get_link_data_fields(self, data: DataDict) -> set[str]:
        """
        Extract field names from data that correspond to links.
        """
        link_fields = set()
        for key, value in data.items():
            if isinstance(value, (HubValueDate, MontrekHubABC)):
                link_fields.add(key)
            elif isinstance(value, (list, QuerySet)):
                if value and any(
                    isinstance(item, (HubValueDate, MontrekHubABC)) for item in value
                ):
                    link_fields.add(key)
        return link_fields

    def _get_link_classes_for_fields(
        self, field_names: set[str]
    ) -> list[type[MontrekLinkABC]]:
        """
        Extract link classes that correspond to specific field names in the data.
        """
        from django.db.models.fields.related import ManyToOneRel

        link_classes = []
        for field in self.db_staller.hub_class._meta.get_fields():
            # Skip fields not in our data
            if field.name not in field_names:
                continue

            through_model = None

            # Handle ManyToMany fields
            if field.many_to_many and hasattr(field, "through"):
                through_model = field.through

            # Handle ManyToOneRel (reverse ForeignKey relations)
            elif isinstance(field, ManyToOneRel):
                through_model = field.related_model
            elif isinstance(field, ManyToManyField):
                through_model = field.remote_field.through

            # Check if it's a MontrekLinkABC subclass
            if (
                through_model
                and hasattr(through_model, "__mro__")
                and any(
                    base.__name__ == "MontrekLinkABC" for base in through_model.__mro__
                )
            ):
                link_classes.append(through_model)

        return link_classes

    def cache_queryset(self, sat_hashes_dict: SatHashesDict):
        cache: HashSatMap = defaultdict()
        now = timezone.now()
        for sat_class, hashes in sat_hashes_dict.items():
            if sat_class.is_timeseries:
                state_date_end_criterion = Q(
                    hub_value_date__hub__state_date_end__gt=now
                )
                relate_fields = ("hub_value_date",)
                hub_id_field = "hub_value_date__hub"
            else:
                state_date_end_criterion = Q(hub_entity__state_date_end__gt=now)
                relate_fields = ("hub_entity",)
                hub_id_field = "hub_entity"
            qs = sat_class.objects.select_related(*relate_fields).filter(
                state_date_end_criterion,
                Q(hash_identifier__in=hashes),
                state_date_start__lte=now,
                state_date_end__gt=now,
            )

            for sat in qs:
                cache[(sat_class, sat.hash_identifier)] = sat
                if sat_class.is_timeseries:
                    hub = sat.hub_value_date.hub
                else:
                    hub = sat.hub_entity
                hub_id = hub.id
                self._cached_hubs.setdefault(hub_id, hub)
                if sat_class.is_timeseries:
                    self._cached_hub_value_dates.setdefault(
                        (hub_id, sat.hub_value_date.value_date_list.value_date),
                        sat.hub_value_date,
                    )
                else:
                    self._cached_hub_value_dates.setdefault(
                        (hub_id, None), sat.hub_entity.hub_value_date
                    )
        cache_queryset = cast(HashSatMap, dict(cache))
        self.cached_queryset = cache_queryset

    def _enrich_data(self):
        self.data["created_by_id"] = self.user_id
        self._upfront_formats()

    def _create_static_satellites(self):
        for sat_class in self.db_staller.get_static_satellite_classes():
            sat = self._create_static_satellite(sat_class)
            if sat is None:
                continue
            self._process_static_satellite(sat)

    def _create_ts_satellites(self):
        for sat_class in self.db_staller.get_ts_satellite_classes():
            sat = self._create_ts_satellite(sat_class)
            if sat is None:
                continue
            self._process_ts_satellite(sat)

    def _create_static_satellite(
        self, sat_class: type[MontrekSatelliteABC]
    ) -> Optional[MontrekSatelliteABC]:
        sat_data = self._get_satellite_data(sat_class)
        if self._is_sat_data_empty(sat_data):
            return None
        return sat_class(
            **sat_data, state_date_start=self.creation_date, hub_entity=self.hub
        )

    def _create_ts_satellite(
        self, sat_class: type[MontrekSatelliteABC]
    ) -> Optional[MontrekSatelliteABC]:
        sat_data = self._get_satellite_data(sat_class)
        if self._is_sat_data_empty(sat_data):
            return None
        return sat_class(
            **sat_data,
            state_date_start=self.creation_date,
            hub_value_date=self.hub_value_date,
        )

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

    def _get_satellite_data(self, sat_class: type[MontrekSatelliteABC]):
        return {
            key: value
            for key, value in self.data.items()
            if key in sat_class.get_value_field_names() + ["created_by_id"]
        }

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
        if value_date in self._cached_value_date_lists:
            self.value_date_list = self._cached_value_date_lists[value_date]
            return
        obj = ValueDateList.objects.filter(value_date=value_date).first()
        if obj is None:
            obj = ValueDateList.objects.create(value_date=value_date)
        self._cached_value_date_lists[value_date] = obj
        self.value_date_list = obj

    def _get_hub_from_data(self):
        """
        Retrieve an existing hub entity from the database if 'hub_entity_id' is provided in self.data.
        Sets self.hub to the corresponding hub instance.
        """
        if "hub_entity_id" in self.data and not pd.isnull(self.data["hub_entity_id"]):
            hub_entity_id = self.data["hub_entity_id"]
            if hub_entity_id in self._cached_hubs:
                self.hub = self._cached_hubs[hub_entity_id]
                return
            self.hub = self.db_staller.hub_class.objects.get(
                id=self.data["hub_entity_id"]
            )
            self._cached_hubs[hub_entity_id] = self.hub

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
            hub_value_date_index = (self.hub.id, self.value_date_list.value_date)
            if hub_value_date_index in self._cached_hub_value_dates:
                self.hub_value_date = self._cached_hub_value_dates[hub_value_date_index]
                return
            existing_hub_value_date = (
                self.db_staller.hub_value_date_class.objects.filter(
                    hub=self.hub, value_date_list=self.value_date_list
                )
            )
            if existing_hub_value_date:
                self.hub_value_date = existing_hub_value_date.get()
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
        if self.cached_queryset is not None:
            return self.cached_queryset.get(
                (satellite_class, sat_hash_identifier), None
            )
        return satellite_class.objects.filter(
            state_date_end_criterion,
            Q(hash_identifier=sat_hash_identifier),
            state_date_start__lte=self.creation_date,
            state_date_end__gt=self.creation_date,
        ).first()

    def _updated_satellite(
        self, sat: MontrekSatelliteABC, existing_sat: MontrekSatelliteABC
    ):
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
            [sat_class in self.updated_satellites for sat_class in self.new_satellites]
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
        latest_sat = (
            sat.__class__.objects.filter(hub_entity_id=self.data["hub_entity_id"])
            .order_by("-state_date_start")
            .first()
        )
        if not latest_sat:
            return

        latest_sat.state_date_end = self.creation_date
        self.db_staller.stall_updated_satellite(latest_sat)

    def _is_sat_data_empty(self, data: DataDict) -> bool:
        data = data.copy()
        data.pop("comment", None)
        data.pop("created_by_id", None)
        data.pop("value_date", None)
        return all(dt is None for dt in data.values())

    def _get_link_data(self) -> dict[str, list[MontrekHubABC]]:
        link_data = {}
        for key, value in self.data.items():
            if isinstance(value, HubValueDate):
                link_data[key] = [value.hub]
            elif isinstance(value, MontrekHubABC):
                link_data[key] = [value]
            elif isinstance(value, (list, QuerySet)):
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
        else:
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
        cache_key = (link_class, self.hub.id, hub_field)
        if cache_key in self._cached_links:
            existing_links = self._cached_links[cache_key]
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
    def __init__(self, db_creator: DbCreator):
        self.db_creator = db_creator
        self.data_collection: list[DataDict] = []
        self.hubs: list[MontrekHubABC | None] = []

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
        sat_hashes: SatHashesDict = defaultdict(set)
        hub_ids = []
        value_dates = []
        for data in self.data_collection:
            hub_id = None
            value_date = None
            if "hub_entity_id" in data:
                hub_id = data["hub_entity_id"]
                if hub_id is not None:
                    hub_ids.append(hub_id)
            if "value_date" in data:
                value_date = data["value_date"]
                value_dates.append(value_date)
        hub_ids = set(hub_ids)
        if value_dates == []:
            value_dates = [None]
        value_dates = set(value_dates)
        self.db_creator.cache_hubs(hub_ids)
        self.db_creator.cache_value_dates(value_dates)
        self.db_creator.cache_hub_value_dates(hub_ids, value_dates)
        for data in self.data_collection:
            sat_hash_map = self.db_creator.get_sat_hashes(data)
            for sat_class, hash_value in sat_hash_map.items():
                sat_hashes[sat_class].add(hash_value)
        sat_hashes = dict(sat_hashes)
        self.db_creator.cache_queryset(sat_hashes)
        link_field_names = set()
        for data in self.data_collection:
            link_data = self.db_creator._get_link_data_fields(data)
            link_field_names.update(link_data)
        if link_field_names:
            self.db_creator.cache_links(link_field_names)

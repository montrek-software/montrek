import datetime
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Iterable, cast

from baseclasses.models import MontrekSatelliteABC, ValueDateList
from baseclasses.repositories.db.db_staller import DbStallerProtocol
from baseclasses.repositories.db.satellite_creator import SatelliteCreator
from baseclasses.repositories.db.typing import (
    DataDict,
    HashSatMap,
    SatHashesDict,
    THubCacheType,
    THubValueDateCacheType,
    TValueDateCacheType,
)
from baseclasses.utils import datetime_to_montrek_time, to_date
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)
HUB_ENTITY_COLUMN = "hub_entity_id"
VALUE_DATE_COLUMN = "value_date"


class DbCreatorCacheBase(ABC):
    satellite_creator_class: type[SatelliteCreator] = SatelliteCreator

    def __init__(self, db_staller: DbStallerProtocol):
        self.db_staller = db_staller
        self.satellite_creator = self.satellite_creator_class()
        self.hub_ids: set[int] = {}
        self.cached_hubs: THubCacheType = {}
        self.cached_value_date_lists: TValueDateCacheType = {}
        self.cached_hub_value_dates: THubValueDateCacheType = {}
        self.cached_queryset: HashSatMap = {}

    @abstractmethod
    def cache_with_data(self, data: Iterable[DataDict]) -> None:
        pass

    def cache_hubs(self):
        logger.debug("Caching %d hubs", len(self.hub_ids))
        hub_class = self.db_staller.hub_class
        hubs = hub_class.objects.filter(id__in=self.hub_ids)
        self.cached_hubs.update({hub.id: hub for hub in hubs})
        logger.debug("End cache hubs")

    def cache_value_dates(self, value_dates: set[datetime.date | None]):
        logger.debug("Start cache value_dates")
        value_dates_lists = ValueDateList.objects.filter(
            Q(value_date__in=value_dates) | Q(value_date__isnull=True)
        )
        self.cached_value_date_lists = {
            value_date.value_date: value_date for value_date in value_dates_lists
        }
        logger.debug("End cache value_dates")

    def cache_hub_value_dates(self, value_dates: set[datetime.date | None]):
        logger.debug("Start cache hub_value_dates")

        hub_value_dates = self.db_staller.hub_value_date_class.objects.select_related(
            "value_date_list", "hub"
        ).filter(
            Q(hub__id__in=self.hub_ids)
            & (
                Q(value_date_list__value_date__in=value_dates)
                | Q(value_date_list__value_date__isnull=True)
            )
        )
        self.cached_hub_value_dates = {
            (hvd.hub_id, hvd.value_date_list.value_date): hvd for hvd in hub_value_dates
        }
        logger.debug("End cache hub_value_dates")

    def get_sat_hashes(self, data: Iterable[DataDict]) -> SatHashesDict:
        sat_hashes = {}

        for sat_class in self.db_staller.get_static_satellite_classes():
            sat_hashes[sat_class] = []
            for data_item in data:
                identifier_string = ""
                for id_field in sat_class.identifier_fields:
                    value = data_item.get(id_field, "")
                    if isinstance(value, (datetime.datetime)):
                        value = datetime_to_montrek_time(value)
                    identifier_string += str(value)
                sat_hash = sat_class.convert_string_to_hash(identifier_string)
                sat_hashes[sat_class].append(sat_hash)
        for sat_class in self.db_staller.get_ts_satellite_classes():
            sat_hashes[sat_class] = []
            for hub_value_date in self.cached_hub_value_dates.values():
                sat_hash = sat_class.convert_string_to_hash(str(hub_value_date.id))
                sat_hashes[sat_class].append(sat_hash)
        return sat_hashes

    def cache_satellites(self, sat_hashes_dict: SatHashesDict):
        cache: HashSatMap = defaultdict()
        now = timezone.now()
        for sat_class, hashes in sat_hashes_dict.items():
            if sat_class.is_timeseries:
                state_date_end_criterion = Q(
                    hub_value_date__hub__state_date_end__gt=now
                )
                relate_fields = ("hub_value_date",)
            else:
                state_date_end_criterion = Q(hub_entity__state_date_end__gt=now)
                relate_fields = ("hub_entity",)
            qs = sat_class.objects.select_related(*relate_fields).filter(
                state_date_end_criterion,
                Q(hash_identifier__in=hashes),
                state_date_start__lte=now,
                state_date_end__gt=now,
            )
            for sat in qs:
                # TODO: collect every information for a second satellite gathering run with hub and hvd information
                cache[(sat_class, sat.hash_identifier)] = sat
                if sat_class.is_timeseries:
                    hub = sat.hub_value_date.hub
                else:
                    hub = sat.hub_entity
                hub_id = hub.id
                self.hub_ids.add(hub_id)
                self.cached_hubs.setdefault(hub_id, hub)
                if sat_class.is_timeseries:
                    self.cached_hub_value_dates.setdefault(
                        (hub_id, sat.hub_value_date.value_date_list.value_date),
                        sat.hub_value_date,
                    )
                else:
                    self.cached_hub_value_dates.setdefault(
                        (hub_id, None), sat.hub_entity.hub_value_date
                    )
        cache_queryset = cast(HashSatMap, dict(cache))
        self.cached_satellites = cache_queryset

    def get_cached_satellite(
        self, satellite_class: type[MontrekSatelliteABC], hash: str
    ) -> MontrekSatelliteABC | None:
        return self.cached_satellites.get((satellite_class, hash))


class DbCreatorCacheHubId(DbCreatorCacheBase):
    def cache_with_data(self, data: Iterable[DataDict]) -> None:
        self.get_hub_ids(data)
        self.cache_hubs()
        value_date_ids = self.get_value_date_ids(data)
        self.cache_value_dates(value_dates=value_date_ids)
        self.cache_hub_value_dates(value_date_ids)
        sat_hashes = self.get_sat_hashes(data)
        self.cache_satellites(sat_hashes)

    def get_hub_ids(self, data: Iterable[DataDict]):
        self.hub_ids = {
            int(value)
            for dt in data
            if (value := dt.get(HUB_ENTITY_COLUMN)) is not None
        }

    def get_value_date_ids(self, data: Iterable[DataDict]) -> set[datetime.date | None]:
        return {to_date(value) for dt in data if (value := dt.get(VALUE_DATE_COLUMN))}


class DbCreatorCacheBlank(DbCreatorCacheBase):
    def cache_with_data(self, data: Iterable[DataDict]) -> None:
        self.cached_hubs = {"Abc": None}


class DbCreatorCacheFactory:
    def __init__(self, columns: Iterable[str]):
        self.columns = set(columns)

    def get_cache_class(self) -> type[DbCreatorCacheBase]:
        if HUB_ENTITY_COLUMN in self.columns:
            return DbCreatorCacheHubId
        return DbCreatorCacheBlank

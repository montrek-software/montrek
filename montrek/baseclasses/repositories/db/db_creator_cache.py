import datetime
import logging
from abc import ABC, abstractmethod
from typing import Iterable

from baseclasses.models import ValueDateList
from baseclasses.repositories.db.db_staller import DbStallerProtocol
from baseclasses.repositories.db.typing import (
    DataDict,
    SatHashesMap,
    THubCacheType,
    THubValueDateCacheType,
    TValueDateCacheType,
)
from baseclasses.utils import to_date
from django.db.models import Q

logger = logging.getLogger(__name__)
HUB_ENTITY_COLUMN = "hub_entity_id"
VALUE_DATE_COLUMN = "value_date"


class DbCreatorCacheBase(ABC):
    def __init__(self, db_staller: DbStallerProtocol):
        self.db_staller = db_staller
        self.cached_hubs: THubCacheType = {}
        self.cached_value_date_lists: TValueDateCacheType = {}
        self.cached_hub_value_dates: THubValueDateCacheType = {}

    @abstractmethod
    def cache_with_data(self, data: Iterable[DataDict]) -> None:
        pass

    def cache_hubs(self, hub_ids: set[int]):
        logger.debug("Caching %d hubs", len(hub_ids))
        hub_class = self.db_staller.hub_class
        hubs = hub_class.objects.filter(id__in=hub_ids)
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
        self.cached_hub_value_dates = {
            (hvd.hub_id, hvd.value_date_list.value_date): hvd for hvd in hub_value_dates
        }
        logger.debug("End cache hub_value_dates")

    def get_sat_hashes(self, data: Iterable[DataDict]) -> SatHashesMap:
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


class DbCreatorCacheHubId(DbCreatorCacheBase):
    def cache_with_data(self, data: Iterable[DataDict]) -> None:
        hub_ids = self.get_hub_ids(data)
        self.cache_hubs(hub_ids)
        value_date_ids = self.get_value_date_ids(data)
        self.cache_value_dates(value_dates=value_date_ids)
        self.cache_hub_value_dates(hub_ids, value_date_ids)

    def get_hub_ids(self, data: Iterable[DataDict]) -> set[int]:
        return {
            value for dt in data if (value := dt.get(HUB_ENTITY_COLUMN)) is not None
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

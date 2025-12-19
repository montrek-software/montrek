import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterable

from baseclasses.models import ValueDateList
from baseclasses.repositories.db.db_creator import DataDict
from baseclasses.repositories.db.db_staller import DbStallerProtocol
from baseclasses.typing import MontrekHubProtocol, ValueDateListProtocol
from django.db.models import Q

logger = logging.getLogger(__name__)
HUB_ENTITY_COLUMN = "hub_entity_id"

type HubCacheType = dict[int, MontrekHubProtocol]


class DbCreatorCacheBase(ABC):
    value_date_list_model: type[ValueDateListProtocol] = ValueDateList

    def __init__(self, db_staller: DbStallerProtocol):
        self.db_staller = db_staller
        self.cached_hubs: HubCacheType = {}

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
        value_dates_lists = self.value_date_list_model.objects.filter(
            Q(value_date__in=value_dates) | Q(value_date__isnull=True)
        )
        self._cached_value_date_lists = {
            value_date.value_date: value_date for value_date in value_dates_lists
        }
        logger.debug("End cache value_dates")


class DbCreatorCacheHubId(DbCreatorCacheBase):
    def cache_with_data(self, data: Iterable[DataDict]) -> None:
        hub_ids = self.get_hub_ids(data)
        self.cache_hubs(hub_ids)

    def get_hub_ids(self, data: Iterable[DataDict]) -> set[int]:
        return {
            value for dt in data if (value := dt.get(HUB_ENTITY_COLUMN)) is not None
        }


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

import logging
from abc import ABC, abstractmethod
from typing import Iterable

from baseclasses.models import MontrekHubProtocol
from baseclasses.repositories.db.db_creator import DataDict
from baseclasses.repositories.db.db_staller import DbStallerProtocol

logger = logging.getLogger(__name__)
HUB_ENTITY_COLUMN = "hub_entity_id"

type HubCacheType = dict[int, MontrekHubProtocol]


class DbCreatorCacheBase(ABC):
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

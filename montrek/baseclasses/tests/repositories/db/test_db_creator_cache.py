from typing import cast

from baseclasses.repositories.db.db_creator_cache import (
    DbCreatorCacheBlank,
    DbCreatorCacheFactory,
    DbCreatorCacheHubId,
)
from baseclasses.repositories.db.db_staller import DbStallerProtocol
from baseclasses.typing import MontrekHubProtocol
from django.test import TestCase


class TestDbCreatorCacheFactory(TestCase):
    def test_get_blank_cache(self):
        cache_factory = DbCreatorCacheFactory(["field_1", "field_2"])
        self.assertEqual(cache_factory.get_cache_class(), DbCreatorCacheBlank)

    def test_get_hub_id_cache(self):
        cache_factory = DbCreatorCacheFactory(["field_1", "field_2", "hub_entity_id"])
        self.assertEqual(cache_factory.get_cache_class(), DbCreatorCacheHubId)


class DummyHubObject:
    def __init__(self, id: int):
        self.id = id


class DummyObjects:
    def filter(self, **kwargs):
        ids = cast(list[int], kwargs.get("id__in"))
        return [DummyHubObject(id=_id) for _id in ids]


class DummyHub(MontrekHubProtocol):
    objects = DummyObjects()


class DummyDbStaller(DbStallerProtocol):
    hub_class = DummyHub


class TestDbCreatorCache(TestCase):
    def setUp(self) -> None:
        db_staller = DummyDbStaller()
        self.cache = DbCreatorCacheHubId(db_staller)
        self.data = [{"hub_entity_id": 1}, {"hub_entity_id": 2}]

    def test_get_hub_ids(self):
        hub_ids = self.cache.get_hub_ids(self.data)
        self.assertEqual(hub_ids, {1, 2})

    def test_cache_hubs(self):
        self.cache.cache_with_data(self.data)
        cached_hubs = self.cache.cached_hubs
        self.assertIsInstance(cached_hubs, dict)
        self.assertEqual(list(cached_hubs.keys()), [1, 2])
        hub_1 = cached_hubs[1]
        self.assertEqual(hub_1.id, 1)

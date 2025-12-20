import datetime
from typing import cast

from baseclasses.repositories.db.db_creator_cache import (
    DbCreatorCacheBlank,
    DbCreatorCacheFactory,
    DbCreatorCacheHubId,
)
from baseclasses.repositories.db.db_staller import DbStallerProtocol
from baseclasses.tests.factories.montrek_factory_schemas import ValueDateListFactory
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
        ValueDateListFactory.create(value_date=None)
        ValueDateListFactory.create(value_date="2025-12-20")
        ValueDateListFactory.create(value_date="2025-12-24")

    def test_cache(self):
        data = [
            {"hub_entity_id": 10, "value_date": "2025-12-20"},
            {"hub_entity_id": 20, "value_date": "2025-12-20"},
        ]
        self.cache.cache_with_data(data)
        self.assertEqual(list(self.cache.cached_hubs.keys()), [10, 20])
        self.assertEqual(
            list(self.cache.cached_value_date_lists.keys()),
            [None, datetime.date(2025, 12, 20)],
        )

    def test_cache_hubs(self):
        self.cache.cache_hubs({10, 20})
        cached_hubs = self.cache.cached_hubs
        self.assertIsInstance(cached_hubs, dict)
        self.assertEqual(list(cached_hubs.keys()), [10, 20])
        hub_1 = cached_hubs[10]
        self.assertEqual(hub_1.id, 10)
        hub_1 = cached_hubs[20]
        self.assertEqual(hub_1.id, 20)

    def test_get_hub_ids(self):
        data = [
            {"hub_entity_id": 1},
            {"hub_entity_id": 2},
        ]
        hub_ids = self.cache.get_hub_ids(data)
        self.assertEqual(hub_ids, {1, 2})

    def test_cache_value_dates(self):
        test_date = datetime.date(2025, 12, 20)
        unknown_date = datetime.date(2025, 12, 25)
        self.cache.cache_value_dates({test_date, unknown_date})
        test_cache = self.cache.cached_value_date_lists
        self.assertEqual(len(test_cache), 2)
        self.assertIn(None, test_cache.keys())
        self.assertIn(test_date, test_cache.keys())
        self.assertNotIn(unknown_date, test_cache.keys())
        self.assertEqual(test_cache[None].value_date, None)
        self.assertEqual(test_cache[test_date].value_date, test_date)

    def test_get_value_date_ids(self):
        data = [
            {
                "value_date": "2025-12-20",
            },
            {"value_date": datetime.datetime(2025, 12, 21)},
            {"value_date": datetime.date(2025, 12, 22)},
            {"value_date": "abc"},
        ]
        value_date_ids = self.cache.get_value_date_ids(data)
        self.assertEqual(len(value_date_ids), 4)
        self.assertIn(None, value_date_ids)
        self.assertIn(datetime.date(2025, 12, 20), value_date_ids)
        self.assertIn(datetime.date(2025, 12, 21), value_date_ids)
        self.assertIn(datetime.date(2025, 12, 22), value_date_ids)

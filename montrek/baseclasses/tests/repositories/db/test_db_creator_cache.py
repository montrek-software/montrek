import datetime
from typing import cast

from baseclasses.repositories.db.db_creator_cache import DbCreatorCache
from baseclasses.repositories.db.db_staller import DbStallerProtocol
from baseclasses.tests.factories.montrek_factory_schemas import ValueDateListFactory
from baseclasses.typing import MontrekHubProtocol
from django.test import TestCase
from django.utils import timezone

# ============================================================
# Dummy ValueDate / HubValueDate
# ============================================================


class DummyValueDateList:
    def __init__(self, value_date):
        self.value_date = value_date


class DummyHubObject:
    def __init__(self, id: int):
        self.id = id
        self.state_date_end = datetime.datetime.max
        self.hub_value_date = None  # set later


class DummyHubValueDate:
    def __init__(self, hub: DummyHubObject, value_date):
        self.id = id(self)
        self.hub = hub
        self.hub_id = hub.id
        self.value_date_list = DummyValueDateList(value_date)


class DummyHubValueDateManager:
    def __init__(self, objects):
        self._objects = objects

    def select_related(self, *args):
        return self

    def filter(self, *args, **kwargs):
        return self._objects


class DummyHubValueDateModel:
    def __init__(self, objects):
        self.objects = DummyHubValueDateManager(objects)


class DummyHubObjects:
    def filter(self, **kwargs):
        ids = cast(list[int], kwargs.get("id__in"))
        return [DummyHubObject(id=i) for i in ids]


class DummyHub(MontrekHubProtocol):
    objects = DummyHubObjects()


# ============================================================
# Dummy ORM manager base
# ============================================================


class DummyManager:
    def __init__(self, objects):
        self._objects = objects

    def select_related(self, *args):
        return self

    def filter(self, *args, **kwargs):
        return self._objects


# ============================================================
# Dummy Satellites (NO Django Model inheritance)
# ============================================================


class DummyStaticSatellite:
    is_timeseries = False
    identifier_fields = ["foo"]

    def __init__(self, hash_identifier, hub_entity):
        self.hash_identifier = hash_identifier
        self.hub_entity = hub_entity
        self.hub_entity_id = hub_entity.id
        self.state_date_start = datetime.datetime.min
        self.state_date_end = datetime.datetime.max

    @classmethod
    def convert_string_to_hash(cls, value: str) -> str:
        return f"static:{value}"

    objects = DummyManager([])


class DummyTimeSeriesSatellite:
    is_timeseries = True
    identifier_fields = []

    def __init__(self, hash_identifier, hub_value_date):
        self.hash_identifier = hash_identifier
        self.hub_value_date = hub_value_date
        self.state_date_start = datetime.datetime.min
        self.state_date_end = datetime.datetime.max

    @classmethod
    def convert_string_to_hash(cls, value: str) -> str:
        return f"ts:{value}"

    objects = DummyManager([])


# ============================================================
# Dummy Links (NO Django Model inheritance)
# ============================================================


class DummyLink:
    def __init__(self, hub_in_id, hub_out_id):
        self.hub_in_id = hub_in_id
        self.hub_out_id = hub_out_id
        self.state_date_start = datetime.datetime.min
        self.state_date_end = datetime.datetime.max

    objects = DummyManager([])


# ============================================================
# Dummy DbStaller
# ============================================================


class DummyDbStaller(DbStallerProtocol):
    hub_class = DummyHub

    def __init__(self, hub_value_dates):
        self.hub_value_date_class = DummyHubValueDateModel(hub_value_dates)

    def get_static_satellite_classes(self):
        return [DummyStaticSatellite]

    def get_ts_satellite_classes(self):
        return [DummyTimeSeriesSatellite]


# ============================================================
# Tests
# ============================================================
class MockDbCreatorCacheNoIntrospection(DbCreatorCache):
    def _get_link_classes_for_fields(self, field_names):
        return [DummyLink]


class TestDbCreatorCache(TestCase):
    def setUp(self):
        hub10 = DummyHubObject(10)
        hub20 = DummyHubObject(20)

        hvd_10_none = DummyHubValueDate(hub10, None)
        hvd_10_date = DummyHubValueDate(hub10, datetime.date(2025, 12, 20))
        hvd_20_date = DummyHubValueDate(hub20, datetime.date(2025, 12, 20))

        hub10.hub_value_date = hvd_10_none
        hub20.hub_value_date = hvd_20_date

        self.hvds = [
            hvd_10_none,
            hvd_10_date,
            hvd_20_date,
        ]

        self.db_staller = DummyDbStaller(self.hvds)
        self.cache = MockDbCreatorCacheNoIntrospection(
            self.db_staller, now=timezone.now()
        )

        ValueDateListFactory.create(value_date=None)
        ValueDateListFactory.create(value_date="2025-12-20")

        hub10 = DummyHubObject(10)

        DummyStaticSatellite.objects._objects = [
            DummyStaticSatellite("static:foo", hub10)
        ]

        DummyTimeSeriesSatellite.objects._objects = [
            DummyTimeSeriesSatellite("ts:1", self.hvds[0])
        ]

        DummyLink.objects._objects = [
            DummyLink(hub_in_id=10, hub_out_id=20),
            DummyLink(hub_in_id=20, hub_out_id=10),
        ]

    def test_cache_satellites(self):
        data = [
            {"hub_entity_id": 10, "foo": "foo", "value_date": None},
        ]

        self.cache.cache_with_data(data)

        static_sat = self.cache.get_cached_satellite(DummyStaticSatellite, "static:foo")
        self.assertIsNotNone(static_sat)
        self.assertEqual(static_sat.hub_entity.id, 10)

        ts_sat = self.cache.get_cached_satellite(DummyTimeSeriesSatellite, "ts:1")
        self.assertIsNotNone(ts_sat)
        self.assertEqual(ts_sat.hub_value_date.hub_id, 10)

    def test_cache_links(self):
        data = [
            {"hub_entity_id": 10},
            {"hub_entity_id": 20},
        ]

        self.cache.cache_with_data(data)

        links_in = self.cache.get_cached_links(DummyLink, 10, "hub_in")
        links_out = self.cache.get_cached_links(DummyLink, 10, "hub_out")

        self.assertEqual(len(links_in), 1)
        self.assertEqual(len(links_out), 1)

        self.assertEqual(links_in[0].hub_in_id, 10)
        self.assertEqual(links_out[0].hub_out_id, 10)

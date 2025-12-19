from baseclasses.repositories.db.db_creator_cache import (
    DbCreatorCacheBlank,
    DbCreatorCacheFactory,
)
from django.test import TestCase


class TestDbCreatorCacheFactory(TestCase):
    def test_get_no_hub_id_cache(self):
        cache_factory = DbCreatorCacheFactory(["field_1", "field_2"])
        self.assertIsInstance(cache_factory.get_cache(), DbCreatorCacheBlank)

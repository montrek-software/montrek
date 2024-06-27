from django.test import TestCase

from file_upload.repositories.field_map_repository import FieldMapRepository
from file_upload.tests.factories.field_map_factories import (
    FieldMapStaticSatelliteFactory,
)


class TestFieldMapRepository(TestCase):
    def setUp(self):
        self.repository = FieldMapRepository()

    def test_std_queryset(self):
        field_map_hub = FieldMapStaticSatelliteFactory()

        queryset = self.repository.std_queryset()

        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().source_field, field_map_hub.source_field)
        self.assertEqual(queryset.first().database_field, field_map_hub.database_field)

    def test_get_source_field(self):
        FieldMapStaticSatelliteFactory(
            source_field="source_field", database_field="database_field"
        )
        source_field = self.repository.get_source_field("database_field")
        self.assertEqual(source_field, "source_field")

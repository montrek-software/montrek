from django.test import TestCase

from file_upload.repositories.field_map_repository import FieldMapRepository
from file_upload.tests.factories.field_map_factories import (
    FieldMapStaticSatelliteFactory,
)
from testing.decorators.add_logged_in_user import add_logged_in_user


class TestFieldMapRepository(TestCase):
    @add_logged_in_user
    def setUp(self):
        self.repository = FieldMapRepository({"user_id": self.user.id})

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

    def test_update_existing_field_map(self):
        FieldMapStaticSatelliteFactory(
            source_field="source_field", database_field="database_field"
        )
        test_queryset = self.repository.std_queryset()
        self.assertEqual(test_queryset.count(), 1)
        self.assertEqual(test_queryset.first().source_field, "source_field")
        self.repository.std_create_object(
            {"source_field": "new_source_field", "database_field": "database_field"}
        )
        test_queryset = self.repository.std_queryset()
        self.assertEqual(test_queryset.count(), 1)
        self.assertEqual(test_queryset.first().source_field, "new_source_field")

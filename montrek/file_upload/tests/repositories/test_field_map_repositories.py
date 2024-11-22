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
        FieldMapStaticSatelliteFactory(step=3, source_field="d", database_field="D")
        FieldMapStaticSatelliteFactory(step=2, source_field="c", database_field="C")
        FieldMapStaticSatelliteFactory(step=1, source_field="b", database_field="B")
        FieldMapStaticSatelliteFactory(step=1, source_field="a", database_field="A")

        queryset = self.repository.receive()

        self.assertEqual(queryset.count(), 4)

        # Expect orderinb by step and source_field
        self.assertEqual(queryset[0].source_field, "d")
        self.assertEqual(queryset[1].source_field, "c")
        self.assertEqual(queryset[2].source_field, "b")
        self.assertEqual(queryset[3].source_field, "a")

        self.assertEqual(queryset[0].database_field, "D")
        self.assertEqual(queryset[1].database_field, "C")
        self.assertEqual(queryset[2].database_field, "B")
        self.assertEqual(queryset[3].database_field, "A")

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
        test_queryset = self.repository.receive()
        self.assertEqual(test_queryset.count(), 1)
        self.assertEqual(test_queryset.first().source_field, "source_field")
        self.repository.std_create_object(
            {"source_field": "new_source_field", "database_field": "database_field"}
        )
        test_queryset = self.repository.receive()
        self.assertEqual(test_queryset.count(), 1)
        self.assertEqual(test_queryset.first().source_field, "new_source_field")

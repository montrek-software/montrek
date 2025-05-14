from django.db import models
from django.test import TestCase
from django.utils import timezone
from baseclasses.utils import montrek_time
from baseclasses.repositories.annotator import Annotator
from baseclasses.models import TestMontrekHub


class MockSubqueryBuilder:
    def __init__(self, satellite_class: type, field: str):
        self.satellite_class = satellite_class
        self.field = field
        self.field_type = models.CharField

    def build(self, reference_date: timezone.datetime) -> str:
        return "Hallo"


class MockSatellite:
    @classmethod
    def get_related_hub_class(cls):
        return TestMontrekHub


class TestAnnotationManager(TestCase):
    def test_subquery_to_annotation(self):
        test_annotator = Annotator(TestMontrekHub)
        test_annotator.subquery_builder_to_annotations(
            ["test", "test2"], MockSatellite, MockSubqueryBuilder
        )
        self.assertEqual(len(test_annotator.annotations), 7)
        reference_date = montrek_time(2024, 11, 7)
        annotations = test_annotator.build(reference_date)
        self.assertEqual(annotations["test"], "Hallo")

    def test_annotations_field_map(self):
        test_annotator = Annotator(TestMontrekHub)
        test_annotator.subquery_builder_to_annotations(
            ["test", "test2"], MockSatellite, MockSubqueryBuilder
        )
        field_map = test_annotator.get_annotated_field_map()
        self.assertEqual(
            field_map,
            {
                "comment": models.CharField,
                "created_at": models.DateTimeField,
                "created_by": models.EmailField,
                "hub_entity_id": models.IntegerField,
                "test": models.CharField,
                "test2": models.CharField,
                "value_date": models.DateTimeField,
            },
        )

    def test_rename_field(self):
        test_annotator = Annotator(TestMontrekHub)
        test_annotator.subquery_builder_to_annotations(
            ["test", "test2"], MockSatellite, MockSubqueryBuilder
        )
        test_sub_queryset = test_annotator.annotations["test"]
        test_annotator.rename_field("test", "test_renamed")
        self.assertEqual(test_annotator.annotations["test_renamed"], test_sub_queryset)
        self.assertNotIn("test", test_annotator.annotations)

    def test_satellite_field_names(self):
        test_annotator = Annotator(TestMontrekHub)
        result = test_annotator.satellite_fields_names()
        self.assertEqual(result, [])

    def test_get_linked_satellite_classes(self):
        test_annotator = Annotator(TestMontrekHub)
        result = test_annotator.get_linked_satellite_classes()
        self.assertEqual(result, [])

    def test_skip_raw_annotations_fields(self):
        test_annotator = Annotator(TestMontrekHub)
        raw_fields = ["value_date"]
        test_annotator.subquery_builder_to_annotations(
            raw_fields, MockSatellite, MockSubqueryBuilder
        )
        for raw_field in raw_fields:
            self.assertNotIsInstance(
                test_annotator.annotations[raw_field], MockSubqueryBuilder
            )

from django.test import TestCase
from django.utils import timezone
from baseclasses.utils import montrek_time
from baseclasses.repositories.annotator import Annotator
from baseclasses.models import TestMontrekHub


class MockSubqueryBuilder:
    def __init__(self, satellite_class: type, field: str):
        self.satellite_class = satellite_class
        self.field = field

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
        self.assertEqual(len(test_annotator.annotations), 4)
        reference_date = montrek_time(2024, 11, 7)
        annotations = test_annotator.build(reference_date)
        self.assertEqual(annotations["test"], "Hallo")

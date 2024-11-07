from django.test import TestCase
from baseclasses.repositories.annotator import Annotator


class MockSubqueryBuilder:
    def __init__(self, satellite_class: type, field: str):
        self.satellite_class = satellite_class
        self.field = field

    def build(self) -> str:
        return "Hallo"


class MockSatellite:
    pass


class TestAnnotationManager(TestCase):
    def test_subquery_to_annotation(self):
        test_annotator = Annotator()
        test_annotator.subquery_builder_to_annotations(
            ["test", "test2"], MockSatellite, MockSubqueryBuilder
        )
        self.assertEqual(len(test_annotator.annotations), 2)
        annotations = test_annotator.build()
        self.assertEqual(annotations["test"], "Hallo")

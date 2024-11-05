from django.test import TestCase
from baseclasses.repositories.annotator import Annotator


class MockSubqueryBuilder:
    def get_subquery(self, field: str) -> object:
        return "Hallo"


class TestAnnotationManager(TestCase):
    def test_subquery_to_annotation(self):
        test_annotator = Annotator()
        test_annotator.query_to_annotations(["test"], MockSubqueryBuilder())
        self.assertEqual(test_annotator.annotations["test"], "Hallo")

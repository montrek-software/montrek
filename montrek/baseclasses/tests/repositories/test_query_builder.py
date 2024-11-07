from datetime import datetime

from django.test import TestCase

from baseclasses.models import TestMontrekHub, TestMontrekSatellite
from baseclasses.repositories.annotator import (
    Annotator,
)
from baseclasses.repositories.query_builder import QueryBuilder
from baseclasses.repositories.subquery_builder import (
    SatelliteSubqueryBuilder,
)
from baseclasses.tests.factories.baseclass_factories import (
    TestMontrekSatelliteFactory,
)


class TestQueryBuilder(TestCase):
    def test_query_builder__build_queryset(self):
        test_sat = TestMontrekSatelliteFactory.create(test_name="Test Name")
        subquery_builder = SatelliteSubqueryBuilder(
            TestMontrekSatellite, "pk", datetime.now()
        )
        annotator = Annotator()
        annotator.query_to_annotations(["test_name"], subquery_builder)
        query_builder = QueryBuilder(TestMontrekHub, annotator)
        test_query = query_builder.build_queryset()
        self.assertEqual(test_query.count(), 1)
        self.assertEqual(test_query.first().test_name, test_sat.test_name)

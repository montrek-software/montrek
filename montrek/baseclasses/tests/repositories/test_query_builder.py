from django.test import TestCase
from django.utils import timezone

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
from baseclasses.utils import montrek_time


class TestQueryBuilder(TestCase):
    def setUp(self):
        self.annotator = Annotator()
        self.query_builder = QueryBuilder(TestMontrekHub, self.annotator)

    def test_query_builder__build_queryset(self):
        reference_date = timezone.now()
        test_sat = TestMontrekSatelliteFactory.create(test_name="Test Name")
        subquery_builder = SatelliteSubqueryBuilder(
            TestMontrekSatellite, "pk", reference_date
        )
        self.annotator.query_to_annotations(["test_name"], subquery_builder)
        test_query = self.query_builder.build_queryset(reference_date)
        self.assertEqual(test_query.count(), 1)
        self.assertEqual(test_query.first().test_name, test_sat.test_name)

    def test_query_builder__build_queryset__no_annotations(self):
        reference_date = timezone.now()
        test_query = self.query_builder.build_queryset(reference_date)
        self.assertEqual(test_query.count(), 0)

    def test_query_builder__build_queryset__with_reference_date(self):
        TestMontrekSatelliteFactory.create(
            test_name="Test Name", hub_entity__state_date_end=montrek_time(2024, 11, 7)
        )
        ref_date_1 = montrek_time(2024, 11, 6)
        ref_date_2 = montrek_time(2024, 11, 8)
        subquery_builder = SatelliteSubqueryBuilder(
            TestMontrekSatellite, "pk", ref_date_2
        )
        self.annotator.query_to_annotations(["test_name"], subquery_builder)
        test_query_1 = self.query_builder.build_queryset(ref_date_1)
        test_query_2 = self.query_builder.build_queryset(ref_date_2)
        self.assertEqual(test_query_1.count(), 1)
        self.assertEqual(test_query_2.count(), 0)

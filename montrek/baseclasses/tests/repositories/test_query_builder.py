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
        self.annotator = Annotator(TestMontrekHub)
        self.query_builder = QueryBuilder(self.annotator, {})
        self.reference_date = timezone.now()

    def test_query_builder__build_queryset(self):
        test_sat = TestMontrekSatelliteFactory.create(test_name="Test Name")
        self.annotator.subquery_builder_to_annotations(
            ["test_name"], TestMontrekSatellite, SatelliteSubqueryBuilder
        )
        test_query = self.query_builder.build_queryset(self.reference_date)
        self.assertEqual(test_query.count(), 1)
        self.assertEqual(test_query.first().test_name, test_sat.test_name)

    def test_query_builder__build_queryset__no_annotations(self):
        test_query = self.query_builder.build_queryset(self.reference_date)
        self.assertEqual(test_query.count(), 0)

    def test_query_builder__build_queryset__with_reference_date(self):
        TestMontrekSatelliteFactory.create(
            test_name="Test Name", hub_entity__state_date_end=montrek_time(2024, 11, 7)
        )
        ref_date_1 = montrek_time(2024, 11, 6)
        ref_date_2 = montrek_time(2024, 11, 8)
        self.annotator.subquery_builder_to_annotations(
            ["test_name"], TestMontrekSatellite, SatelliteSubqueryBuilder
        )
        test_query_1 = self.query_builder.build_queryset(ref_date_1)
        test_query_2 = self.query_builder.build_queryset(ref_date_2)
        self.assertEqual(test_query_1.count(), 1)
        self.assertEqual(test_query_2.count(), 0)

    def test_query_builder__build_queryset__with_filter(self):
        TestMontrekSatelliteFactory.create(
            test_name="Test Name 0",
            test_value=0,
        )
        TestMontrekSatelliteFactory.create(
            test_name="Test Name 1",
            test_value=1,
        )
        self.annotator.subquery_builder_to_annotations(
            ["test_name", "test_value"], TestMontrekSatellite, SatelliteSubqueryBuilder
        )
        filter_dict = {
            "filter": {
                "": {"test_value__exact": {"filter_value": 0, "filter_negate": False}}
            }
        }
        query_builder = QueryBuilder(self.annotator, session_data=filter_dict)
        test_query = query_builder.build_queryset(self.reference_date)
        self.assertEqual(test_query.count(), 1)
        self.assertEqual(test_query.first().test_name, "Test Name 0")

from django.db.models import Q
from django.test import TestCase
from django.utils import timezone

from baseclasses.models import TestMontrekHub, TestMontrekSatellite
from baseclasses.repositories.montrek_repository import MontrekRepository
from baseclasses.tests.factories.baseclass_factories import TestMontrekSatelliteFactory


class MockMontrekRepository(MontrekRepository):
    def set_annotations(self):
        pass


class TestRepository(MontrekRepository):
    hub_class = TestMontrekHub
    default_order_fields: tuple[str] = ("test_name",)

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            TestMontrekSatellite,
            ["test_name", "test_value"],
        )


class TestMontrekRepository(TestCase):
    def test_set_annotation_riases_error(self):
        with self.assertRaises(NotImplementedError) as cm:
            MontrekRepository()
        self.assertEqual(
            cm.exception.args[0],
            "set_annotations is not implemented for MontrekRepository",
        )

    def test_session_date_default(self):
        montrek_repo = MockMontrekRepository()
        session_start_date = montrek_repo.session_start_date
        session_end_date = montrek_repo.session_end_date
        self.assertEqual(session_start_date.date(), timezone.datetime.min.date())
        self.assertTrue(session_start_date.tzinfo is not None)
        self.assertEqual(session_end_date.date(), timezone.datetime.max.date())
        self.assertTrue(session_end_date.tzinfo is not None)

    def test_session_date_set(self):
        montrek_repo = MockMontrekRepository(
            session_data={"start_date": "2020-01-01", "end_date": "2020-02-01"}
        )
        session_start_date = montrek_repo.session_start_date
        session_end_date = montrek_repo.session_end_date
        self.assertEqual(
            session_start_date.date(), timezone.datetime(2020, 1, 1).date()
        )
        self.assertTrue(session_start_date.tzinfo is not None)
        self.assertEqual(session_end_date.date(), timezone.datetime(2020, 2, 1).date())
        self.assertTrue(session_end_date.tzinfo is not None)

    def test_session_user_id(self):
        self.assertIsNone(MockMontrekRepository().session_user_id)
        self.assertEqual(MockMontrekRepository({"user_id": 1}).session_user_id, 1)

    def test_query_filter(self):
        montrek_repo = MockMontrekRepository(
            session_data={
                "request_path": "/path/",
                "filter": {
                    "/path/": {
                        "field1__exact": {
                            "filter_negate": False,
                            "filter_value": "value1",
                        }
                    }
                },
            }
        )
        test_query = montrek_repo.query_builder.query_filter

        self.assertTrue(isinstance(test_query, Q))
        self.assertEqual(test_query.__dict__, Q(Q(field1__exact="value1")).__dict__)

        montrek_repo.session_data["filter"]["/path/"]["field1__exact"][
            "filter_negate"
        ] = True
        test_query = montrek_repo.query_builder.query_filter

        self.assertTrue(isinstance(test_query, Q))
        self.assertEqual(test_query.__dict__, (Q(~Q(field1__exact="value1"))).__dict__)

    def test_receive__order_list(self):
        TestMontrekSatelliteFactory.create(test_name="ZZZ", test_value=1)
        TestMontrekSatelliteFactory.create(test_name="AAA", test_value=2)
        TestMontrekSatelliteFactory.create(test_name="MMM", test_value=3)
        montrek_repo = TestRepository(session_data={})
        test_query_set = montrek_repo.receive()
        self.assertEqual(
            [test.test_name for test in test_query_set],
            ["AAA", "MMM", "ZZZ"],
        )
        montrek_repo.set_order_fields(["-test_value"])
        self.assertEqual(
            [test.test_name for test in montrek_repo.receive()],
            ["MMM", "AAA", "ZZZ"],
        )

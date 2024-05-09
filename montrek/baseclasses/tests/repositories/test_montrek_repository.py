from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.test import TestCase
from django.utils import timezone
from baseclasses.repositories.montrek_repository import MontrekRepository


class TestMontrekRepository(TestCase):
    def test_session_date_default(self):
        montrek_repo = MontrekRepository()
        session_start_date = montrek_repo.session_start_date
        session_end_date = montrek_repo.session_end_date
        self.assertEqual(session_start_date.date(), timezone.datetime.min.date())
        self.assertTrue(session_start_date.tzinfo is not None)
        self.assertEqual(session_end_date.date(), timezone.datetime.max.date())
        self.assertTrue(session_end_date.tzinfo is not None)

    def test_session_date_set(self):
        montrek_repo = MontrekRepository(
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
        self.assertIsNone(MontrekRepository().session_user_id)
        self.assertEqual(MontrekRepository({"user_id": 1}).session_user_id, 1)

    def test_query_filter(self):
        montrek_repo = MontrekRepository(
            session_data={
                "request_path": "/path/",
                "filter": {
                    "/path/": {
                        "field1__equal": {
                            "filter_negate": False,
                            "filter_value": "value1",
                        }
                    }
                },
            }
        )
        q_list = montrek_repo.query_filter

        self.assertTrue(isinstance(q_list, list))
        self.assertEqual(len(q_list), 1)
        self.assertTrue(isinstance(q_list[0], Q))
        self.assertEqual(q_list[0].__dict__, Q(field1__equal="value1").__dict__)

        montrek_repo = MontrekRepository(
            session_data={
                "request_path": "/path/",
                "filter": {
                    "/path/": {
                        "field1__equal": {
                            "filter_negate": True,
                            "filter_value": "value1",
                        }
                    }
                },
            }
        )
        q_list = montrek_repo.query_filter

        self.assertTrue(isinstance(q_list, list))
        self.assertEqual(len(q_list), 1)
        self.assertTrue(isinstance(q_list[0], Q))
        self.assertEqual(q_list[0].__dict__, (~Q(field1__equal="value1")).__dict__)

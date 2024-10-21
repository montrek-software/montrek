from django.db.models import Q
from django.test import TestCase
from django.utils import timezone
from baseclasses.repositories.montrek_repository import MontrekRepository

from dataclasses import dataclass
from baseclasses.errors.montrek_user_error import MontrekError


@dataclass
class FakeHub:
    id: int
    fake_db_field: str | None


class FakeRepository(MontrekRepository):
    def std_queryset(self):
        return [
            FakeHub(1, "a"),
            FakeHub(2, "b"),
            FakeHub(3, "c"),
            FakeHub(4, "c"),
            FakeHub(5, ""),
            FakeHub(6, None),
        ]


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
                        "field1__exact": {
                            "filter_negate": False,
                            "filter_value": "value1",
                        }
                    }
                },
            }
        )
        test_query = montrek_repo.query_filter

        self.assertTrue(isinstance(test_query, Q))
        self.assertEqual(test_query.__dict__, Q(Q(field1__exact="value1")).__dict__)

        montrek_repo.session_data["filter"]["/path/"]["field1__exact"][
            "filter_negate"
        ] = True
        test_query = montrek_repo.query_filter

        self.assertTrue(isinstance(test_query, Q))
        self.assertEqual(test_query.__dict__, (Q(~Q(field1__exact="value1"))).__dict__)

    def test_get_hubs_for_values(self):
        values = ["a", "b", "c", "d", "e"]
        repository = FakeRepository()
        actual = repository.get_hubs_for_values(
            values=values,
            by_repository_field="fake_db_field",
            raise_for_multiple_hubs=False,
            raise_for_unmapped_values=False,
        )
        actual_ids = [hub.id if hub else None for hub in actual]
        expected_ids = [1, 2, 4, None, None]  # 4 is the second hub with value "c"
        self.assertEqual(actual_ids, expected_ids)

    def test_get_hubs_for_values_raises_error_for_multiple_hubs(self):
        values = ["a", "b", "c", "d", "e"]
        repository = FakeRepository()
        with self.assertRaisesMessage(
            MontrekError, "Multiple hubs found for values (truncated): c"
        ):
            repository.get_hubs_for_values(
                values=values,
                by_repository_field="fake_db_field",
                raise_for_multiple_hubs=True,
                raise_for_unmapped_values=False,
            )

    def test_get_hubs_for_values_raises_error_for_unmapped_values(self):
        values = ["a", "b", "c", "d", "e"]
        repository = FakeRepository()
        with self.assertRaisesMessage(
            MontrekError, "Cannot find hub for values (truncated): d, e"
        ):
            repository.get_hubs_for_values(
                values=values,
                by_repository_field="fake_db_field",
                raise_for_multiple_hubs=False,
                raise_for_unmapped_values=True,
            )

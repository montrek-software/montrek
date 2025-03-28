from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils import timezone
from baseclasses.utils import (
    TableMetaSessionData,
    montrek_time,
    montrek_today,
    montrek_date_string,
    get_date_range_dates,
    get_content_type,
)
from freezegun import freeze_time


class TestMontrekTime(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def create_request_with_session(self):
        request = self.factory.get("/")  # Create a request object
        middleware = SessionMiddleware(lambda: None)
        middleware.process_request(request)
        request.session.save()
        return request

    def test_montrek_time(self):
        mtime = montrek_time(2023, 10, 1)
        self.assertEqual(mtime.date(), timezone.datetime(2023, 10, 1).date())

    @freeze_time("2023-10-01")
    def test_montrek_today(self):
        self.assertEqual(montrek_today(), timezone.datetime(2023, 10, 1).date())

    def test_montrek_date_string(self):
        self.assertEqual(
            montrek_date_string(timezone.datetime(2023, 10, 1)), "2023-10-01"
        )

    @freeze_time("2023-01-01")
    def test_default_dates(self):
        request = self.create_request_with_session()

        expected_start_date = "2022-12-02"  # Adjust based on your date calculation
        expected_end_date = "2023-01-01"

        start_date, end_date = get_date_range_dates(request)
        self.assertEqual(start_date, expected_start_date)
        self.assertEqual(end_date, expected_end_date)

    @freeze_time("2023-01-01")
    def test_session_dates(self):
        request = self.create_request_with_session()
        request.session = {"start_date": "2022-12-15", "end_date": "2023-01-10"}

        expected_start_date = "2022-12-15"
        expected_end_date = "2023-01-10"

        start_date, end_date = get_date_range_dates(request)
        self.assertEqual(start_date, expected_start_date)
        self.assertEqual(end_date, expected_end_date)


class TestGetContentType(TestCase):
    def test_get_content_type(self):
        self.assertEqual(get_content_type("test.pdf"), "application/pdf")
        self.assertEqual(get_content_type("test.txt"), "text/plain")
        self.assertEqual(get_content_type("test.csv"), "text/csv")
        self.assertEqual(get_content_type("test.zip"), "application/zip")
        self.assertEqual(get_content_type("test"), "application/octet-stream")
        self.assertEqual(
            get_content_type("test.xlsx"),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


class MockRequest:
    def __init__(self) -> None:
        self.path = "/"


class TestTableMetaSessionData(TestCase):
    def test__get_filters_isnull(self):
        test_table_meta_session_data = TableMetaSessionData(MockRequest())
        test_data = test_table_meta_session_data._get_filters(
            {"filter_lookup": ["isnull"], "filter_field": ["test_field"]}
        )
        self.assertTrue(test_data["filter"]["/"]["test_field__isnull"]["filter_value"])

    def test__get_filters_true(self):
        test_table_meta_session_data = TableMetaSessionData(MockRequest())
        for true_value in ("True", "true", True):
            test_data = test_table_meta_session_data._get_filters(
                {
                    "filter_lookup": ["test"],
                    "filter_field": ["test_field"],
                    "filter_value": [true_value],
                }
            )
            self.assertTrue(
                test_data["filter"]["/"]["test_field__test"]["filter_value"]
            )

    def test__get_filters_false(self):
        test_table_meta_session_data = TableMetaSessionData(MockRequest())
        for false_value in ("False", "false", False):
            test_data = test_table_meta_session_data._get_filters(
                {
                    "filter_lookup": ["test"],
                    "filter_field": ["test_field"],
                    "filter_value": [false_value],
                }
            )
            self.assertFalse(
                test_data["filter"]["/"]["test_field__test"]["filter_value"]
            )

    def test__get_filters_and(self):
        test_table_meta_session_data = TableMetaSessionData(MockRequest())
        test_data = test_table_meta_session_data._get_filters(
            {
                "filter_lookup": ["test", "and_test"],
                "filter_field": ["test_field", "sub_field"],
                "filter_value": ["test_value", "sub_test_value"],
            }
        )
        self.assertEqual(
            test_data["filter"]["/"]["test_field__test"]["filter_value"], "test_value"
        )
        self.assertEqual(
            test_data["filter"]["/"]["sub_field__and_test"]["filter_value"],
            "sub_test_value",
        )

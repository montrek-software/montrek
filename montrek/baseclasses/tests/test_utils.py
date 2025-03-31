from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils import timezone
from baseclasses.utils import (
    FilterCountMetaSessionDataElement,
    FilterMetaSessionDataElement,
    PagesMetaSessionDataElement,
    PaginateByMetaSessionDataElement,
    TableMetaSessionData,
    IsCompactFormatMetaSessionDataElement,
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
        self.path = "/test-path/"
        self.session = {}


class TestFilterMetaSessionDataElement(TestCase):
    def setUp(self):
        self.request = MockRequest()

    def test__get_filters_isnull(self):
        session_data = {"filter_lookup": ["isnull"], "filter_field": ["test_field"]}
        test_element = FilterMetaSessionDataElement(session_data, self.request)
        test_data = test_element.apply_data()
        self.assertTrue(
            test_data["filter"]["/test-path/"]["test_field__isnull"]["filter_value"]
        )

    def test__get_filters_true(self):
        for true_value in ("True", "true", True):
            session_data = {
                "filter_lookup": ["test"],
                "filter_field": ["test_field"],
                "filter_value": [true_value],
            }
            test_element = FilterMetaSessionDataElement(session_data, self.request)
            test_data = test_element.apply_data()
            self.assertTrue(
                test_data["filter"]["/test-path/"]["test_field__test"]["filter_value"]
            )

    def test__get_filters_false(self):
        for false_value in ("False", "false", False):
            session_data = {
                "filter_lookup": ["test"],
                "filter_field": ["test_field"],
                "filter_value": [false_value],
            }
            test_element = FilterMetaSessionDataElement(session_data, self.request)
            test_data = test_element.apply_data()
            self.assertFalse(
                test_data["filter"]["/test-path/"]["test_field__test"]["filter_value"]
            )

    def test__get_filters_and(self):
        session_data = {
            "filter_lookup": ["test", "and_test"],
            "filter_field": ["test_field", "sub_field"],
            "filter_value": ["test_value", "sub_test_value"],
        }
        test_element = FilterMetaSessionDataElement(session_data, self.request)
        test_data = test_element.apply_data()
        self.assertEqual(
            test_data["filter"]["/test-path/"]["test_field__test"]["filter_value"],
            "test_value",
        )
        self.assertEqual(
            test_data["filter"]["/test-path/"]["sub_field__and_test"]["filter_value"],
            "sub_test_value",
        )

    def test_get_filters_multiple_conditions(self):
        """Test getting filters with multiple conditions"""

        session_data = {
            "filter_field": ["name", "age"],
            "filter_lookup": ["icontains", "gte"],
            "filter_value": ["John", "18"],
        }

        test_element = FilterMetaSessionDataElement(session_data, self.request)
        filter_data = test_element.apply_data()

        self.assertIn("/test-path/", filter_data["filter"])
        filters = filter_data["filter"]["/test-path/"]

        self.assertIn("name__icontains", filters)
        self.assertIn("age__gte", filters)

    def test_get_filters_boolean_values(self):
        """Test filters with boolean values"""

        # Test true values
        session_data = {
            "filter_field": ["is_active"],
            "filter_lookup": ["exact"],
            "filter_value": ["True"],
        }

        test_element = FilterMetaSessionDataElement(session_data, self.request)
        filter_data = test_element.apply_data()
        bool_filter = filter_data["filter"]["/test-path/"]["is_active__exact"]

        self.assertTrue(bool_filter["filter_value"])
        self.assertFalse(bool_filter["filter_negate"])

    def test_get_filters_negation(self):
        """Test filter negation"""

        session_data = {
            "filter_field": ["status"],
            "filter_lookup": ["exact"],
            "filter_value": ["pending"],
            "filter_negate": ["true"],
        }

        test_element = FilterMetaSessionDataElement(session_data, self.request)
        filter_data = test_element.apply_data()
        negate_filter = filter_data["filter"]["/test-path/"]["status__exact"]

        self.assertEqual(negate_filter["filter_value"], "pending")
        self.assertTrue(negate_filter["filter_negate"])

    def test_get_filters_in_lookup(self):
        """Test 'in' lookup type for filters"""
        session_data = {
            "filter_field": ["status"],
            "filter_lookup": ["in"],
            "filter_value": ["active,pending"],
        }

        test_element = FilterMetaSessionDataElement(session_data, self.request)
        filter_data = test_element.apply_data()
        in_filter = filter_data["filter"]["/test-path/"]["status__in"]

        self.assertEqual(in_filter["filter_value"], ["active", "pending"])

    def test_get_filters_isnull_lookup(self):
        """Test 'isnull' lookup type"""

        session_data = {
            "filter_field": ["end_date"],
            "filter_lookup": ["isnull"],
            "filter_value": [""],
        }

        test_element = FilterMetaSessionDataElement(session_data, self.request)
        filter_data = test_element.apply_data()
        isnull_filter = filter_data["filter"]["/test-path/"]["end_date__isnull"]

        self.assertTrue(isnull_filter["filter_value"])


class TestPagesMetaSessionDataElement(TestCase):
    def setUp(self):
        self.request = MockRequest()

    def test_get_page_number_existing(self):
        """Test getting existing page number"""

        session_data = {"pages": {"/test-path/": 3}, "page": 5}
        test_element = PagesMetaSessionDataElement(session_data, self.request)

        page_data = test_element.apply_data()

        self.assertEqual(page_data["pages"]["/test-path/"], 5)

    def test_get_page_number_default(self):
        """Test page number when no page is specified"""

        session_data = {}
        test_element = PagesMetaSessionDataElement(session_data, self.request)

        page_data = test_element.apply_data()

        self.assertIn("pages", page_data)
        self.assertEqual(page_data["pages"], {})


class TestFilterCountMetaSessionDataElement(TestCase):
    def setUp(self):
        self.request = MockRequest()

    def test_get_filter_form_count(self):
        """Test filter form count incrementation"""

        session_data = {}
        test_element = FilterCountMetaSessionDataElement(session_data, self.request)

        count_data = test_element.apply_data()

        self.assertIn("filter_count", count_data)
        self.assertEqual(count_data["filter_count"]["/test-path/"], 1)


class TestPaginateByCountMetaSessionDataElement(TestCase):
    def setUp(self):
        self.request = MockRequest()

    def test_get_paginate_by(self):
        """Test paginate_by"""

        session_data = {}
        test_element = PaginateByMetaSessionDataElement(session_data, self.request)
        test_data = test_element.apply_data()

        self.assertIn("paginate_by", test_data)
        self.assertEqual(test_data["paginate_by"]["/test-path/"], 10)

    def test_get_pageinate_by_existing(self):
        """Test getting existing paginate_by"""

        session_data = {"paginate_by": {"/test-path/": 15}}
        test_element = PaginateByMetaSessionDataElement(session_data, self.request)
        test_data = test_element.apply_data()

        self.assertEqual(test_data["paginate_by"]["/test-path/"], 15)

    def test_get_pageinate_not_below_five(self):
        """Test getting existing paginate_by"""

        session_data = {"paginate_by": {"/test-path/": 4}}

        test_element = PaginateByMetaSessionDataElement(session_data, self.request)
        test_data = test_element.apply_data()

        self.assertEqual(test_data["paginate_by"]["/test-path/"], 5)
        session_data = {"paginate_by": {"/test-path/": 0}}
        test_element = PaginateByMetaSessionDataElement(session_data, self.request)
        test_data = test_element.apply_data()

        self.assertEqual(test_data["paginate_by"]["/test-path/"], 5)
        session_data = {"paginate_by": {"/test-path/": -5}}
        test_element = PaginateByMetaSessionDataElement(session_data, self.request)
        test_data = test_element.apply_data()

        self.assertEqual(test_data["paginate_by"]["/test-path/"], 5)


class TestIsCompactFormatCountMetaSessionDataElement(TestCase):
    def setUp(self):
        self.request = MockRequest()

    def test_is_comapct_format(self):
        """Test paginate_by"""

        session_data = {}
        test_element = IsCompactFormatMetaSessionDataElement(session_data, self.request)
        test_data = test_element.apply_data()

        self.assertIn("is_compact_format", test_data)
        self.assertEqual(test_data["is_compact_format"]["/test-path/"], False)

    def test_is_comapct_format__set(self):
        """Test paginate_by"""

        session_data = {"is_compact_format": {"/test-path/": True}}
        test_element = IsCompactFormatMetaSessionDataElement(session_data, self.request)
        test_data = test_element.apply_data()

        self.assertIn("is_compact_format", test_data)
        self.assertEqual(test_data["is_compact_format"]["/test-path/"], True)


class TestTableMetaSessionData(TestCase):
    def setUp(self):
        self.request = MockRequest()

    def test_init(self):
        """Test initialization of TableMetaSessionData"""
        table_meta = TableMetaSessionData(self.request)
        self.assertEqual(table_meta.request, self.request)

    def test_update_session_data_basic(self):
        """Test basic update of session data"""
        table_meta = TableMetaSessionData(self.request)

        # Prepare initial session data
        session_data = {
            "filter_field": ["name"],
            "filter_lookup": ["icontains"],
            "filter_value": ["test"],
        }

        # Update session data
        updated_data = table_meta.update_session_data(session_data)

        # Verify session updates
        self.assertIn("filter", self.request.session)
        self.assertIn("pages", self.request.session)
        self.assertIn("filter_count", self.request.session)
        self.assertIn("paginate_by", self.request.session)
        self.assertIn("is_compact_format", self.request.session)

    def test_update_session_data_empty_input(self):
        """Test update with empty session data"""
        table_meta = TableMetaSessionData(self.request)

        session_data = {}

        updated_data = table_meta.update_session_data(session_data)

        self.assertEqual(self.request.session["filter"], {})
        self.assertEqual(self.request.session["pages"], {})
        self.assertEqual(self.request.session["filter_count"], {"/test-path/": 1})
        self.assertEqual(self.request.session["paginate_by"], {"/test-path/": 10})
        self.assertEqual(
            self.request.session["is_compact_format"], {"/test-path/": False}
        )

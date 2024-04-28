from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db.models import QuerySet
from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages import get_messages
from dataclasses import dataclass
from baseclasses.views import MontrekViewMixin
from baseclasses.views import MontrekListView
from baseclasses.dataclasses.montrek_message import (
    MontrekMessageError,
    MontrekMessageInfo,
)
from baseclasses.pages import MontrekPage
from baseclasses.managers.montrek_manager import MontrekManager
from reporting.managers.montrek_table_manager import MontrekTableManager
from reporting.dataclasses import table_elements as te


class MockQuerySet:
    def __init__(self, *args):
        self.items = args

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]

    def __eq__(self, other):
        if isinstance(other, list):
            return list(self.items) == other
        return NotImplemented

    def all(self):
        return self.items


@dataclass
class MockData:
    field: str
    value: int


class MockRepository:
    def __init__(self, session_data):
        self.session_data = session_data
        self.messages = []

    def std_queryset(self):
        return MockQuerySet(
            MockData("item1", 1), MockData("item2", 2), MockData("item3", 3)
        )  # Dummy data for testing


class MockRequester:
    def add_mock_request(self, url: str):
        self.request = RequestFactory().get(url)
        self.request.user = AnonymousUser()
        session_middleware = SessionMiddleware(lambda request: None)
        session_middleware.process_request(self.request)
        self.request.session.save()
        message_middleware = MessageMiddleware(lambda request: None)
        message_middleware.process_request(self.request)


class MockManager(MontrekTableManager):
    repository_class = MockRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(attr="field", name="Field"),
            te.IntTableElement(attr="value", name="Value"),
            te.LinkTableElement(
                name="Link",
                url="home",
                kwargs={},
                hover_text="Link",
                icon="icon",
            ),
        ]


class MockMontrekView(MontrekViewMixin, MockRequester):
    manager_class = MockManager

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)


class MockPage(MontrekPage):
    @property
    def tabs(self):
        return []


class TestUnderConstruction(TestCase):
    def test_under_construction(self):
        response = self.client.get("/under_construction")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "under_construction.html")


class TestMontrekViewMixin(TestCase):
    def test_session_data(self):
        mock_view = MockMontrekView("/")
        self.assertEqual(
            mock_view.session_data, {"filter_field": "", "filter_value": ""}
        )

    def test_session_data_with_query_params(self):
        mock_view = MockMontrekView("/?param1=value1&param2=value2")
        expected_data = {
            "param1": ["value1"],
            "param2": ["value2"],
            "filter_field": "",
            "filter_value": "",
        }
        self.assertEqual(mock_view.session_data, expected_data)

    def test_session_data_storage(self):
        mock_view = MockMontrekView("/")
        mock_view.request.session["test_key"] = "test_value"
        self.assertEqual(mock_view.session_data["test_key"], "test_value")

    def test_session_data_contains_user_id_for_authenticated_user(self):
        user = get_user_model().objects.create_user(
            email="test@example.com", password="test"
        )
        mock_view = MockMontrekView("/")
        mock_view.request.user = user
        self.assertEqual(mock_view.session_data["user_id"], user.id)

    def test_session_data_contains_no_user_id_for_anonymous_user(self):
        mock_view = MockMontrekView("/")
        self.assertNotIn("user_id", mock_view.session_data)

    def test_filter_data_handling(self):
        mock_view = MockMontrekView("/?filter_field=field1&filter_value=value1")
        expected_filter_data = {
            "filter_field": "field1",
            "filter_value": "value1",
            "filter": {"field1": "value1"},
        }
        self.assertEqual(mock_view.session_data, expected_filter_data)

    def test_repository_object_creation(self):
        mock_view = MockMontrekView("/")
        self.assertIsInstance(mock_view.manager.repository, MockRepository)

    def test_show_repository_messages(self):
        mock_view = MockMontrekView("/")
        mock_view.manager.messages = [
            MontrekMessageError("Error message"),
            MontrekMessageInfo("Info message"),
        ]
        mock_view.show_messages()
        # Retrieve messages from the request
        messages = list(get_messages(mock_view.request))

        # Assert that the messages contain the expected content
        self.assertTrue(
            any(
                msg.message == "Error message" and msg.level_tag == "error"
                for msg in messages
            )
        )
        self.assertTrue(
            any(
                msg.message == "Info message" and msg.level_tag == "info"
                for msg in messages
            )
        )

    def test_elements_property(self):
        mock_view = MockMontrekView("/")
        self.assertEqual(mock_view.elements, [])

    def test_get_view_queryset(self):
        mock_view = MockMontrekView("/")
        mock_queryset = mock_view.get_view_queryset()
        self.assertEqual(
            [mqe.field for mqe in mock_queryset], ["item1", "item2", "item3"]
        )


class MockMontrekListView(MontrekListView, MockRequester):
    manager_class = MockManager
    page_class = MockPage
    kwargs = {}

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)


class MockManagerPdfFails(MontrekTableManager):
    def to_latex(self):
        return "\\textbf{This is a bold text with a missing closing brace."


class MockMontrekListViewPdfFails(MontrekListView, MockRequester):
    manager_class = MockManagerPdfFails
    page_class = MockPage
    kwargs = {}

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)


class TestMontrekListView(TestCase):
    def test_list_view_base_normal_load(self):
        """
        Test that the page loads normally without the `gen_csv` query parameter.
        """
        test_list_view = MockMontrekListView("dummy")
        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 200)

    def test_list_view_base_csv_generation(self):
        test_list_view = MockMontrekListView("dummy?gen_csv=true")
        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertTrue(
            response["Content-Disposition"].startswith(
                'attachment; filename="export.csv"'
            )
        )

    def test_list_view_base_pdf_generation(self):
        test_list_view = MockMontrekListView("dummy?gen_pdf=true")
        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_list_view_base_pdf_generation__fails(self):
        test_list_view = MockMontrekListViewPdfFails("dummy?gen_pdf=true")
        response = test_list_view.get(test_list_view.request)
        self.assertEqual(response.status_code, 302)
        self.assertGreater(len(test_list_view.manager.messages), 0)

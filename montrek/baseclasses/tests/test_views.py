from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages import get_messages
from baseclasses.views import MontrekViewMixin
from baseclasses.dataclasses.montrek_message import MontrekMessageError, MontrekMessageInfo


class MockRepository:
    def __init__(self, session_data):
        self.session_data = session_data
        self.messages = []

    def std_queryset(self):
        return ["item1", "item2", "item3"]  # Dummy data for testing



class MockMontrekView(MontrekViewMixin):
    repository = MockRepository

    def __init__(self, url: str):
        super().__init__()
        self.add_mock_request(url)

    def add_mock_request(self, url: str):
        self.request = RequestFactory().get(url)
        session_middleware = SessionMiddleware(lambda request: None)
        session_middleware.process_request(self.request)
        self.request.session.save()
        message_middleware = MessageMiddleware(lambda request: None)
        message_middleware.process_request(self.request)


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
        mock_view = MockMontrekView('/?param1=value1&param2=value2')
        expected_data = {'param1': ['value1'], 'param2': ['value2'], 'filter_field': '', 'filter_value': ''}
        self.assertEqual(mock_view.session_data, expected_data)

    def test_session_data_storage(self):
        mock_view = MockMontrekView('/')
        mock_view.request.session['test_key'] = 'test_value'
        self.assertEqual(mock_view.session_data['test_key'], 'test_value')

    def test_filter_data_handling(self):
        mock_view = MockMontrekView('/?filter_field=field1&filter_value=value1')
        expected_filter_data = {'filter_field': 'field1', 'filter_value': 'value1', 'filter': {'field1': 'value1'}}
        self.assertEqual(mock_view.session_data, expected_filter_data)

    def test_repository_object_creation(self):
        mock_view = MockMontrekView('/')
        self.assertIsInstance(mock_view.repository_object, MockRepository)

    def test_show_repository_messages(self):
        mock_view = MockMontrekView('/')
        mock_view.repository_object.messages = [
            MontrekMessageError("Error message"),
            MontrekMessageInfo("Info message"),
        ]
        mock_view.show_repository_messages()
        # Retrieve messages from the request
        messages = list(get_messages(mock_view.request))

        # Assert that the messages contain the expected content
        self.assertTrue(any(msg.message == "Error message" and msg.level_tag == "error" for msg in messages))
        self.assertTrue(any(msg.message == "Info message" and msg.level_tag == "info" for msg in messages))

    def test_elements_property(self):
        mock_view = MockMontrekView('/')
        self.assertEqual(mock_view.elements, [])

    def test_get_std_queryset(self):
        mock_view = MockMontrekView('/')
        self.assertEqual(mock_view._get_std_queryset(), ["item1", "item2", "item3"])

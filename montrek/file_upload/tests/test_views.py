from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from file_upload.views import MontrekUploadFileView
from baseclasses.pages import MontrekPage


class MockPage(MontrekPage):
    def get_tabs(self):
        return []


class MockFileUploadView(MontrekUploadFileView):
    page_class = MockPage

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


class TestMontrekUploadFileView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = MockFileUploadView("/fake-url/")

    def test_show_correct_url(self):
        test_file_upload_view = self.view
        response = test_file_upload_view.get(self.view.request)
        self.assertEqual(response.status_code, 200)

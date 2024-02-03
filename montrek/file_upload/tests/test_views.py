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

    # TODO Write tests after implementation
    # def test_get_context_data(self):
    #    self.assertEqual(self.view.response.status_code, 200)
    #    self.assertIn('form', response.context_data)
    #    self.assertIsInstance(response.context_data['form'], UploadFileForm)

    # def test_post_with_valid_form(self):
    #    file = BytesIO(b"My file contents")
    #    file.name = 'test.txt'
    #    data = {'file': file}

    #    request = self.factory.post('/fake-url/', data)
    #    response = self.view(request)
    #    self.assertEqual(response.status_code, 200)
    #    # Add more assertions here to validate the response

    # def test_post_with_invalid_form(self):
    #    data = QueryDict('')
    #    request = self.factory.post('/fake-url/', data)
    #    response = self.view(request)
    #    self.assertEqual(response.status_code, 200)  # Assuming the view returns 200 with the form errors
    #    self.assertFalse(response.context_data['form'].is_valid())

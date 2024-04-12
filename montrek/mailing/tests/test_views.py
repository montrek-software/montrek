from django.test import TestCase
from mailing.tests.factories.mailing_factories import MailSatelliteFactory
from mailing import views
from mailing.forms import MailingSendForm
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class TestMailsOverview(TestCase):
    def setUp(self):
        MailSatelliteFactory.create_batch(3)

    def test_view_and_query(self):
        view = views.MailOverviewListView()
        object_list = view.get_view_queryset()
        self.assertEqual(len(object_list), 3)

    def test_view_page(self):
        view = views.MailOverviewListView()
        view.kwargs = {}
        page_context = view.get_page_context({})
        self.assertNotEqual(page_context["page_title"], "page_title not set!")
        self.assertNotEqual(page_context["title"], "No Title set!")

    def test_account_overview_returns_correct_html(self):
        response = self.client.get("/mailing/overview")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_table.html")

    def test_account_overview_context_data(self):
        response = self.client.get("/mailing/overview")
        context = response.context
        object_list = context["object_list"]
        self.assertEqual(len(object_list), 3)
        self.assertIsInstance(context["view"], views.MailOverviewListView)


class MockManager:
    def __init__(self, session_data: dict):
        pass

    def send_mail(self, data: dict):
        pass


class MockSendMailView(views.SendMailView):
    manager_class = MockManager


class TestSendMailView(TestCase):
    def setUp(self) -> None:
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)

    def test_view_page(self):
        view = views.SendMailView()
        view.kwargs = {}
        page_context = view.get_page_context({})
        self.assertNotEqual(page_context["page_title"], "page_title not set!")
        self.assertNotEqual(page_context["title"], "No Title set!")

    def test_send_mail(self):
        class MockForm:
            cleaned_data: dict = {}

        view = MockSendMailView()
        mock_form = MockForm()
        response = view.form_valid(mock_form)
        self.assertEqual(response.url, "/mailing/overview")

    def test_view_form(self):
        view = views.SendMailView()
        self.assertEqual(view.form_class, MailingSendForm)

    def test_account_overview_returns_correct_html(self):
        response = self.client.get("/mailing/send")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_create.html")

from django.test import TestCase
from mailing.tests.factories.mailing_factories import MailSatelliteFactory
from mailing import views
from mailing.forms import MailingSendForm
from baseclasses.managers.montrek_manager import MontrekManager
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from testing.test_cases import view_test_cases as vtc


class TestMailsOverview(vtc.MontrekListViewTestCase):
    viewname = "mailing"
    view_class = views.MailOverviewListView
    expected_no_of_rows = 3

    def build_factories(self):
        MailSatelliteFactory.create_batch(3)


class MockManager(MontrekManager):
    def send_montrek_mail(self, recipients: str, subject: str, message: str):
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
            cleaned_data: dict = {
                "mail_recipients": "a@b.de",
                "mail_subject": "Test",
                "mail_message": "This is a test",
            }

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


class TestMailDetailsView(TestCase):
    def setUp(self):
        self.mail = MailSatelliteFactory()

    def test_view_page(self):
        view = views.MailDetailView()
        view.kwargs = {"pk": self.mail.pk}
        page_context = view.get_page_context({})
        self.assertNotEqual(page_context["page_title"], "page_title not set!")
        self.assertNotEqual(page_context["title"], "No Title set!")

    def test_account_overview_returns_correct_html(self):
        response = self.client.get(f"/mailing/{self.mail.pk}/details")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_details.html")

    def test_account_overview_context_data(self):
        response = self.client.get(f"/mailing/{self.mail.pk}/details")
        context = response.context
        self.assertEqual(context["object"], self.mail.hub_entity)
        self.assertIsInstance(context["view"], views.MailDetailView)

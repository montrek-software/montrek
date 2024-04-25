from django.test import TestCase
from mailing.tests.factories.mailing_factories import MailSatelliteFactory
from mailing import views
from mailing.forms import MailingSendForm
from baseclasses.managers.montrek_manager import MontrekManager
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from testing.test_cases import view_test_cases as vtc


class TestMailListViewOverview(vtc.MontrekListViewTestCase):
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


class TestSendMailView(vtc.MontrekViewTestCase):
    viewname = "send_mail"
    view_class = views.SendMailView

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


class TestMailDetailsView(vtc.MontrekDetailViewTestCase):
    viewname = "mail_detail"
    view_class = views.MailDetailView

    def build_factories(self):
        self.mail = MailSatelliteFactory()

    def url_kwargs(self):
        return {"pk": self.mail.hub_entity.pk}

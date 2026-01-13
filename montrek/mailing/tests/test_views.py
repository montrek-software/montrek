from baseclasses.managers.montrek_manager import MontrekManager
from django.conf import settings
from django.core import mail
from mailing import views
from mailing.forms import MailingSendForm
from mailing.tests.factories.mailing_factories import MailSatelliteFactory
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
    expected_mail_template = "montrek_mail_template"
    expected_success_url = "/mailing/overview"

    def test_send_mail(self):
        class MockForm:
            cleaned_data: dict = {
                "mail_recipients": "a@b.de",
                "mail_subject": "Test",
                "mail_message": "This is a test",
            }

        mock_form = MockForm()
        response = self.view.form_valid(mock_form)
        self.assertEqual(response.url, self.expected_success_url)
        test_message = str(mail.outbox[0].message())
        self.assertIn("This is a test", test_message)
        self.assertEqual(mail.outbox[0].subject, "Test")
        self.assertEqual(mail.outbox[0].to, ["a@b.de"])
        with open(
            settings.BASE_DIR
            / f"mailing/templates/mail_templates/{self.expected_mail_template}.html"
        ) as f:
            template = f.read()
            template_start = template.find("<body>")
            self.assertIn(template[:template_start], test_message)
        self.additional_assertions()

    def test_view_form(self):
        view = views.SendMailView()
        self.assertEqual(view.form_class, MailingSendForm)

    def additional_assertions(self):
        # Method con be overwritten in child test cases
        ...

    def test_send_mail_bcc(self):
        class MockForm:
            cleaned_data: dict = {
                "mail_recipients": "a@b.de",
                "mail_subject": "Test",
                "mail_message": "This is a test",
                "mail_bcc": "d@c.de,t@a.fr",
            }

        mock_form = MockForm()
        response = self.view.form_valid(mock_form)
        self.assertEqual(response.url, self.expected_success_url)
        self.assertEqual(mail.outbox[0].bcc, ["d@c.de", "t@a.fr"])


class TestMailDetailsView(vtc.MontrekDetailViewTestCase):
    viewname = "mail_detail"
    view_class = views.MailDetailView

    def build_factories(self):
        self.mail = MailSatelliteFactory()

    def url_kwargs(self):
        return {"pk": self.mail.hub_entity.pk}

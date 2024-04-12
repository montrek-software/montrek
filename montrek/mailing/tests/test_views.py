from django.test import TestCase
from mailing.tests.factories.mailing_factories import MailSatelliteFactory
from mailing import views


class MailsOverview(TestCase):
    def setUp(self):
        MailSatelliteFactory.create_batch(3)

    def test_view(self):
        view = views.MailOverviewListView()
        object_list = view.get_queryset()
        self.assertEqual(len(object_list), 3)

    def test_account_overview_returns_correct_html(self):
        response = self.client.get("mailing/overview")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_table.html")

    def test_account_overview_context_data(self):
        response = self.client.get("mailing/overview")
        context = response.context
        object_list = context["object_list"]
        self.assertEqual(len(object_list), 3)
        self.assertIsInstance(context["view"], views.MailOverview)
        self.assertEqual(context["page_title"], "Send Mails")

import os
import pandas as pd

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from company.repositories.company_repository import CompanyRepository
from company.tests.factories.company_factories import (
    CompanyStaticSatelliteFactory,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from django.core import mail


class TestCompanyOverview(TestCase):
    def test_company_overview_returns_correct_html(self):
        url = reverse("company")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_table.html")


class TestCompanyCreateView(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)

    def test_company_create_returns_correct_html(self):
        url = reverse("company_create")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_create.html")

    def test_view_post_success(self):
        url = reverse("company_create")
        response = self.client.post(
            url,
            {
                "company_name": "Apple",
                "bloomberg_ticker": "APPL",
                "effectual_company_id": "APPL:XNYS",
                "value_date": "2023-01-01",
                "total_revenue": 100.0,
            },
        )
        self.assertEqual(response.status_code, 302)
        company = CompanyRepository().std_queryset().first()
        self.assertEqual(company.company_name, "Apple")
        self.assertEqual(company.bloomberg_ticker, "APPL")
        self.assertEqual(company.effectual_company_id, "APPL:XNYS")
        self.assertEqual(
            company.asset_time_series_satellite.first().total_revenue, 100.0
        )


class TestCompanyDetailsView(TestCase):
    def test_company_details_returns_correct_html(self):
        company = CompanyStaticSatelliteFactory()
        url = reverse("company_details", kwargs={"pk": company.hub_entity.id})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_details.html")


class TestCompanyUpdateView(TestCase):
    def test_company_update_returns_correct_html(self):
        company = CompanyStaticSatelliteFactory()
        url = reverse("company_update", kwargs={"pk": company.hub_entity.id})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_create.html")


class TestCompanyDeleteView(TestCase):
    def test_company_delete_returns_correct_html(self):
        company = CompanyStaticSatelliteFactory()
        url = reverse("company_delete", kwargs={"pk": company.hub_entity.id})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_delete.html")


class TestCompanyTSTableView(TestCase):
    def test_company_ts_table_returns_correct_html(self):
        company = CompanyStaticSatelliteFactory()
        url = reverse("company_ts_table", kwargs={"pk": company.hub_entity.id})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_table.html")

    def test_company_ts_table_returns_correct_data(self):
        company = CompanyStaticSatelliteFactory()
        url = reverse("company_ts_table", kwargs={"pk": company.hub_entity.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_table.html")


class TestRgsCompanyUploadFileView(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)

    def test_company_upload_file_returns_correct_html(self):
        url = reverse("company_upload_file")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "upload_form.html")

    def test_company_upload_file_view_post_success(self):
        url = reverse("company_upload_file")
        test_file_path = os.path.join(
            settings.BASE_DIR, "company", "tests", "data", "rgs_test_small.xlsx"
        )
        test_file_df = pd.read_excel(test_file_path)
        test_file_df = test_file_df.sort_values("Year").drop_duplicates(
            subset=["Company_identifier"], keep="last"
        )
        test_file_df = test_file_df.set_index("Company_identifier")

        with open(test_file_path, "rb") as f:
            data = {"file": f}
            response = self.client.post(
                url,
                data,
                follow=True,
            )
        messages = list(response.context["messages"])

        companies = CompanyRepository().std_queryset()

        self.assertRedirects(response, reverse("company_view_uploads"))
        self.assertEqual(len(companies), test_file_df.shape[0])

        for c in companies:
            expected = test_file_df.loc[c.effectual_company_id].to_dict()
            self.assertEqual(c.company_name, expected["name"])
            self.assertEqual(c.bloomberg_ticker, str(expected["ticker"]))
            self.assertEqual(float(c.total_revenue), float(expected["total_revenue"]))

        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "Upload background task started. You will receive an email when the task is finished.",
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertEqual(mail.outbox[0].subject, "RGS File Upload Terminated")
        self.assertEqual(
            mail.outbox[0].body,
            "RGS upload was successfull (uploaded 56 rows).",
        )


class TestCompanyUploadView(TestCase):
    def test_company_upload_returns_correct_html(self):
        url = reverse("company_view_uploads")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_table.html")


class TestCompanyHistoryView(TestCase):
    def test_company_history_returns_correct_html(self):
        company = CompanyStaticSatelliteFactory()
        url = reverse("company_history", kwargs={"pk": company.hub_entity.id})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_table.html")

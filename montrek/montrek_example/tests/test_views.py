import datetime
import os
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import cast
from unittest.mock import patch

from baseclasses.dataclasses.alert import AlertEnum
from baseclasses.utils import montrek_time
from bs4 import BeautifulSoup, Tag
from django.contrib.auth.models import Permission
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from file_upload.managers.file_upload_manager import TASK_SCHEDULED_MESSAGE
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from montrek_example import views as me_views
from montrek_example.models.example_models import LinkHubBHubD
from montrek_example.repositories.hub_a_repository import (
    HubAFileUploadRegistryRepository,
    HubARepository,
)
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.repositories.hub_d_repository import HubDRepository
from montrek_example.tests.factories import montrek_example_factories as me_factories
from reporting.managers.montrek_table_manager import MontrekTablePaginator
from testing.decorators import add_logged_in_user
from testing.decorators.mock_external_get import mock_external_get
from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekDeleteViewTestCase,
    MontrekDetailViewTestCase,
    MontrekDownloadViewTestCase,
    MontrekFileResponseTestCase,
    MontrekListViewTestCase,
    MontrekRedirectViewTestCase,
    MontrekReportFieldEditViewTestCase,
    MontrekReportViewTestCase,
    MontrekRestApiViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekViewTestCase,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class TestMontrekExampleAListView(MontrekListViewTestCase):
    viewname = "montrek_example_a_list"
    view_class = me_views.MontrekExampleAList
    expected_no_of_rows = 1

    def build_factories(self):
        sata1 = me_factories.SatA1Factory()
        me_factories.SatA2Factory(hub_entity=sata1.hub_entity)

    def test_filter(self):
        other_sata1 = me_factories.SatA1Factory()
        me_factories.SatA2Factory(
            hub_entity=other_sata1.hub_entity, field_a2_str="test"
        )
        repo = HubARepository()
        repo.store_in_view_model()
        self.assertEqual(len(repo.receive()), 2)

        url = reverse(
            "montrek_example_a_list",
        )
        self.client.get(url, data={"refresh_data": "true"})
        response = self.client.get(url)
        obj_list = response.context_data["object_list"]

        self.assertEqual(len(obj_list), 2)
        query_params = {
            "filter_field": "field_a2_str",
            "filter_lookup": "in",
            "filter_negate": False,
            "filter_value": "test,foo,bar",
        }
        response = self.client.get(url, data=query_params)
        obj_list = response.context_data["object_list"]
        self.assertEqual(len(obj_list), 1)
        self.assertEqual(obj_list[0].hub.id, other_sata1.hub_entity.id)

        # The filter should persist for this path until reset
        response = self.client.get(url)
        obj_list = response.context_data["object_list"]
        self.assertEqual(len(obj_list), 1)
        self.assertEqual(obj_list[0].hub.id, other_sata1.hub_entity.id)

        response = self.client.get(url, data={"action": "reset"}, follow=True)
        obj_list = response.context_data["object_list"]
        self.assertRedirects(response, url)
        self.assertEqual(len(obj_list), 2)

    def test_overview(self):
        response = self.client.get(self.url)
        overview_html = response.context_data["overview"]
        exp_overview_html = ""
        self.assertEqual(overview_html, exp_overview_html)


class TestMontrekExampleAListViewPages(MontrekListViewTestCase):
    viewname = "montrek_example_a_list"
    view_class = me_views.MontrekExampleAList
    expected_no_of_rows = 10

    def build_factories(self):
        for i in range(15):
            me_factories.SatA2Factory.create(field_a2_str=f"field_{i}")

    def test_selected_and_remember_pages(self):
        query_params = {"page": 2}
        response = self.client.get(self.url, data=query_params)
        test_page = response.context_data["paginator"]
        self.assertIsInstance(test_page, MontrekTablePaginator)
        self.assertEqual(test_page.number, 2)
        response = self.client.get(self.url)
        test_page = response.context_data["paginator"]
        self.assertIsInstance(test_page, MontrekTablePaginator)
        self.assertEqual(test_page.number, 2)

    def test_apply_filter_on_latter_page(self):
        query_params = {"page": 2}
        response = self.client.get(self.url, data=query_params)
        query_params = {
            "filter_field": "field_a2_str",
            "filter_value": "field_12",
            "filter_negate": "False",
            "filter_lookup": "exact",
            "action": "filter",
        }
        response = self.client.get(self.url, data=query_params)
        object_list = response.context_data["object_list"]
        self.assertEqual(len(object_list), 1)
        self.assertEqual(object_list[0].field_a2_str, "field_12")
        test_page = response.context_data["paginator"]
        self.assertEqual(test_page.number, 1)


class TestMontrekExampleACreateView(MontrekCreateViewTestCase):
    viewname = "montrek_example_a_create"
    view_class = me_views.MontrekExampleACreate

    def creation_data(self):
        return {
            "field_a1_str": "test",
            "field_a1_int": 1,
            "field_a2_str": "test2",
            "field_a2_float": 2.0,
        }

    def test_validation_error(self):
        # The validator on field_a1_int should only allow values between -1000 and 1000
        data = self.creation_data()
        data["field_a1_int"] = 1001
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Ensure this value is less than or equal to 1000."
        )
        data["field_a1_int"] = -1001
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Ensure this value is greater than or equal to -1000."
        )


class TestMontrekExampleCreateReturn(TestCase):
    @add_logged_in_user
    def test_remember_http_referer(self):
        start_url = reverse("under_construction")
        response_start = self.client.get(start_url)
        self.assertEqual(response_start.status_code, 200)
        create_url = reverse(
            "montrek_example_a_create",
        )
        response_create = self.client.get(create_url, HTTP_REFERER=start_url)
        self.assertEqual(response_create.status_code, 200)
        return_create = self.client.post(
            create_url,
            {
                "field_a1_str": "test",
                "field_a1_int": 1,
                "field_a2_str": "test2",
                "field_a2_float": 2.0,
            },
        )
        self.assertEqual(return_create.status_code, 302)
        self.assertRedirects(
            return_create,
            start_url,
        )

    @add_logged_in_user
    def test_no_http_referer(self):
        start_url = reverse("under_construction")
        response_start = self.client.get(start_url)
        self.assertEqual(response_start.status_code, 200)
        create_url = reverse(
            "montrek_example_a_create",
        )
        response_create = self.client.get(create_url)
        self.assertEqual(response_create.status_code, 200)
        return_create = self.client.post(
            create_url,
            {
                "field_a1_str": "test",
                "field_a1_int": 1,
                "field_a2_str": "test2",
                "field_a2_float": 2.0,
            },
        )
        self.assertEqual(return_create.status_code, 302)
        expected_url = reverse("montrek_example_a_list")
        self.assertRedirects(
            return_create,
            expected_url,
        )


class TestMontrekExampleUpdateReturn(TestCase):
    @add_logged_in_user
    def test_remember_http_referer(self):
        start_url = reverse("under_construction")
        response_start = self.client.get(start_url)
        self.assertEqual(response_start.status_code, 200)
        self.sat_a1 = me_factories.SatA1Factory()
        me_factories.SatA2Factory(hub_entity=self.sat_a1.hub_entity)
        HubARepository().store_in_view_model()
        update_url = reverse(
            "montrek_example_a_update",
            kwargs={"pk": self.sat_a1.get_hub_value_date().id},
        )
        response_update = self.client.get(update_url, HTTP_REFERER=start_url)
        self.assertEqual(response_update.status_code, 200)
        return_update = self.client.post(
            update_url,
            {
                "field_a1_str": "test",
                "field_a1_int": 1,
                "field_a2_str": "test2",
                "field_a2_float": 2.0,
            },
        )
        self.assertEqual(return_update.status_code, 302)
        self.assertRedirects(
            return_update,
            start_url,
        )

    @add_logged_in_user
    def test_no_http_referer(self):
        start_url = reverse("under_construction")
        response_start = self.client.get(start_url)
        self.assertEqual(response_start.status_code, 200)
        self.sat_a1 = me_factories.SatA1Factory()
        me_factories.SatA2Factory(hub_entity=self.sat_a1.hub_entity)
        HubARepository().store_in_view_model()
        update_url = reverse(
            "montrek_example_a_update",
            kwargs={"pk": self.sat_a1.get_hub_value_date().id},
        )
        response_update = self.client.get(update_url)
        self.assertEqual(response_update.status_code, 200)
        return_update = self.client.post(
            update_url,
            {
                "field_a1_str": "test",
                "field_a1_int": 1,
                "field_a2_str": "test2",
                "field_a2_float": 2.0,
            },
        )
        self.assertEqual(return_update.status_code, 302)
        expected_url = reverse("montrek_example_a_list")
        self.assertRedirects(
            return_update,
            expected_url,
        )


class TestMontrekExampleAUpdateView(MontrekUpdateViewTestCase):
    viewname = "montrek_example_a_update"
    view_class = me_views.MontrekExampleAUpdate

    def build_factories(self):
        self.sat_a1 = me_factories.SatA1Factory(field_a1_str="test")
        me_factories.SatA1Factory(field_a1_str="dummy")
        me_factories.SatA2Factory(hub_entity=self.sat_a1.hub_entity)
        self.sat_b1 = me_factories.SatB1Factory()
        me_factories.SatB2Factory(hub_entity=self.sat_b1.hub_entity)
        self.sat_a1.hub_entity.link_hub_a_hub_b.add(self.sat_b1.hub_entity)
        HubBRepository().store_in_view_model()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_a1.get_hub_value_date().id}

    def update_data(self):
        return {
            "field_a1_str": "test_update",
            "field_a1_int": 2,
            "field_a2_str": "test2_update",
            "field_a2_float": 3.0,
        }

    def test_initial_links_in_form(self):
        response = self.client.get(self.url)
        form = response.context["form"]
        self.assertEqual(form.initial["field_a1_str"], "test")
        self.assertEqual(form["link_hub_a_hub_b"].value(), self.sat_b1.hub_entity.pk)


class TestMontrekExampleReportView(MontrekReportViewTestCase):
    expected_number_of_report_elements = 3
    viewname = "montrek_example_report"
    view_class = me_views.MontrekExampleReport


class TestMontrekExampleAReportView(MontrekReportViewTestCase):
    expected_number_of_report_elements = 3
    viewname = "montrek_example_a_report"
    view_class = me_views.MontrekExampleAReport

    def build_factories(self):
        self.sat_a1 = me_factories.SatA1Factory(field_a1_str="test")

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_a1.get_hub_value_date().id}


class TestMontrekExampleAReportFieldEditView(MontrekReportFieldEditViewTestCase):
    viewname = "montrek_example_a_edit_field"
    view_class = me_views.MontrekExampleAReportFieldEditView
    update_field = "field_a1_str"
    updated_content = "Updated Field"

    def build_factories(self):
        self.sat_a1 = me_factories.SatA1Factory(field_a1_str="test", field_a1_int=12)

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_a1.get_hub_value_date().id}

    def additional_assertions(self, created_object):
        self.assertEqual(created_object.field_a1_int, 12)


class TestMontrekExampleAReportFieldEditViewInt(MontrekReportFieldEditViewTestCase):
    viewname = "montrek_example_a_edit_field"
    view_class = me_views.MontrekExampleAReportFieldEditView
    update_field = "field_a1_int"
    updated_content = 13

    def build_factories(self):
        self.sat_a1 = me_factories.SatA1Factory(field_a1_str="test", field_a1_int=12)

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_a1.get_hub_value_date().id}

    def additional_assertions(self, created_object):
        self.assertEqual(created_object.field_a1_str, "test")


class TestMontrekExampleADownloadView(MontrekDownloadViewTestCase):
    viewname = "montrek_example_a_download"
    view_class = me_views.MontrekExampleADownloadView

    def expected_filename(self) -> str:
        return "example_md.txt"

    def additional_download_assertions(self):
        self.assertEqual(
            self.response.content.decode(),
            "| A1 String   | A1 Int   | A2 String   | A2 Float   | B1 String   | TestField   |\n|-------------|----------|-------------|------------|-------------|-------------|",
        )


class TestMontrekExampleADetailView(MontrekDetailViewTestCase):
    viewname = "montrek_example_a_details"
    view_class = me_views.MontrekExampleADetails

    def build_factories(self):
        self.hub_vd_0 = me_factories.AHubValueDateFactory(value_date=None)
        me_factories.SatA1Factory(hub_entity=self.hub_vd_0.hub)
        self.hub_vd = me_factories.AHubValueDateFactory(value_date=None)
        me_factories.SatA1Factory(hub_entity=self.hub_vd.hub)

    def url_kwargs(self) -> dict:
        return {"pk": self.hub_vd.hub.id}

    def test_overview(self):
        response = self.client.get(self.url)
        overview_html = response.context_data["overview"]

        soup = BeautifulSoup(overview_html, "html.parser")

        # ---- High-level structure ----
        container = soup.find("div", class_="row scrollable-content")
        self.assertIsNotNone(container)

        form = container.find("form", method="get")
        self.assertIsNotNone(form)

        hidden_input = form.find(
            "input",
            {
                "type": "hidden",
                "name": "order_action",
                "id": "form-order_by-action",
            },
        )
        self.assertIsNotNone(hidden_input)

        table = form.find("table")
        self.assertIsNotNone(table)
        self.assertIn("table-custom-striped", table["class"])

        # ---- Headers ----
        headers = table.find_all("th")
        self.assertEqual(len(headers), 2)

        header_expectations = [
            ("", "A1 String"),
            ("field_a1_int", "A1 Int"),
        ]

        for th, (attr, label) in zip(headers, header_expectations, strict=False):
            self.assertEqual(th["title"], attr)

            button = th.find("button", class_="btn-order-field")
            self.assertIsNotNone(button)

            self.assertEqual(
                button["onclick"],
                f"document.getElementById('form-order_by-action').value='{attr}'",
            )

            text = " ".join(button.get_text(strip=True).split())
            self.assertEqual(text, label)

        # ---- Body rows ----
        rows = table.tbody.find_all("tr")
        self.assertEqual(len(rows), 2)

        for row, hub in zip(rows, [self.hub_vd_0, self.hub_vd], strict=False):
            link = row.find("a")
            self.assertIsNotNone(link)

            self.assertEqual(link["id"], f"id__montrek_example_a_{hub.hub_id}_details")
            self.assertEqual(link["href"], f"/montrek_example/a/{hub.hub_id}/details")
            self.assertEqual(link.text.strip(), "DEFAULT")

            cells = row.find_all("td")
            self.assertEqual(cells[1].text.strip(), "0")


class TestMontrekExampleADelete(MontrekDeleteViewTestCase):
    viewname = "montrek_example_a_delete"
    view_class = me_views.MontrekExampleADelete

    def build_factories(self):
        self.sata1 = me_factories.SatA1Factory()
        me_factories.SatA2Factory(hub_entity=self.sata1.hub_entity)

    def url_kwargs(self) -> dict:
        return {"pk": self.sata1.get_hub_value_date().id}


class TestMontrekExampleDeleteReturn(TestCase):
    @add_logged_in_user
    def test_remember_http_referer(self):
        start_url = reverse("under_construction")
        response_start = self.client.get(start_url)
        self.assertEqual(response_start.status_code, 200)
        self.sata1 = me_factories.SatA1Factory()
        me_factories.SatA2Factory(hub_entity=self.sata1.hub_entity)
        delete_url = reverse(
            "montrek_example_a_delete",
            kwargs={"pk": self.sata1.get_hub_value_date().id},
        )
        response_delete = self.client.get(delete_url, HTTP_REFERER=start_url)
        self.assertEqual(response_delete.status_code, 200)
        return_delete = self.client.post(delete_url)
        self.assertEqual(return_delete.status_code, 302)
        self.assertRedirects(
            return_delete,
            start_url,
        )

    @add_logged_in_user
    def test_no_http_referer(self):
        start_url = reverse("under_construction")
        response_start = self.client.get(start_url)
        self.assertEqual(response_start.status_code, 200)
        self.sata1 = me_factories.SatA1Factory()
        me_factories.SatA2Factory(hub_entity=self.sata1.hub_entity)
        delete_url = reverse(
            "montrek_example_a_delete",
            kwargs={"pk": self.sata1.get_hub_value_date().id},
        )
        response_delete = self.client.get(delete_url)
        self.assertEqual(response_delete.status_code, 200)
        return_delete = self.client.post(delete_url)
        self.assertEqual(return_delete.status_code, 302)
        expected_url = reverse("montrek_example_a_list")
        self.assertRedirects(
            return_delete,
            expected_url,
        )

    @add_logged_in_user
    def test_enforce_success_url(self):
        start_url = reverse("under_construction")
        response_start = self.client.get(start_url)
        self.assertEqual(response_start.status_code, 200)
        self.sata1 = me_factories.SatD1Factory()
        delete_url = reverse(
            "montrek_example_d_delete",
            kwargs={"pk": self.sata1.get_hub_value_date().id},
        )
        response_delete = self.client.get(delete_url, HTTP_REFERER=start_url)
        self.assertEqual(response_delete.status_code, 200)
        return_delete = self.client.post(delete_url)
        self.assertEqual(return_delete.status_code, 302)
        expected_url = reverse("montrek_example_d_list")
        self.assertRedirects(
            return_delete,
            expected_url,
        )


class TestMontrekExampleAHistoryView(MontrekViewTestCase):
    viewname = "montrek_example_a_history"
    view_class = me_views.MontrekExampleAHistory

    def build_factories(self):
        self.sat = me_factories.SatA1Factory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat.get_hub_value_date().id}

    def test_view_with_history_data(self):
        user1 = MontrekUserFactory()
        user2 = MontrekUserFactory()
        sat = me_factories.SatA1Factory(
            field_a1_str="TestFeld",
            field_a1_int=5,
            state_date_end=montrek_time(2024, 2, 17),
            created_by=user1,
            comment="initial comment",
        )
        me_factories.SatA1Factory(
            hub_entity=sat.hub_entity,
            field_a1_str="TestFeld",
            field_a1_int=6,
            state_date_start=montrek_time(2024, 2, 17),
            created_by=user2,
            comment="change comment",
        )
        me_factories.SatA2Factory(
            hub_entity=sat.hub_entity,
            field_a2_str="ConstantTestFeld",
            field_a2_float=6.0,
            created_by=user2,
            comment="another comment",
        )
        url = reverse(
            "montrek_example_a_history", kwargs={"pk": sat.get_hub_value_date().id}
        )
        self.store_in_view_model()
        response = self.client.get(url)
        test_history_data_tables = response.context_data["history_data_tables"]
        self.assertEqual(len(test_history_data_tables), 3)
        sat_a1_queryset = test_history_data_tables[0].queryset
        self.assertEqual(len(sat_a1_queryset), 2)
        self.assertEqual(sat_a1_queryset[1].field_a1_int, 5)
        self.assertEqual(sat_a1_queryset[0].field_a1_int, 6)
        self.assertEqual(sat_a1_queryset[0].comment, "change comment")
        self.assertEqual(sat_a1_queryset[1].comment, "initial comment")

        self.assertEqual(sat_a1_queryset[0].changed_by, user2.email)
        self.assertEqual(sat_a1_queryset[1].changed_by, user1.email)
        sat_a2_queryset = test_history_data_tables[1].queryset
        self.assertEqual(len(sat_a2_queryset), 1)
        self.assertEqual(sat_a2_queryset[0].field_a2_float, 6.0)
        self.assertEqual(sat_a2_queryset[0].comment, "another comment")
        self.assertEqual(sat_a2_queryset[0].changed_by, user2.email)


class TestMontrekExampleCHistoryView(MontrekViewTestCase):
    viewname = "montrek_example_c_history"
    view_class = me_views.MontrekExampleCHistory

    def build_factories(self):
        self.sat = me_factories.SatC1Factory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat.get_hub_value_date().id}


class TestMontrekExampleBListView(MontrekListViewTestCase):
    viewname = "montrek_example_b_list"
    view_class = me_views.MontrekExampleBList
    expected_no_of_rows = 1

    def build_factories(self):
        satb1fac = me_factories.SatB1Factory()
        me_factories.SatB2Factory(hub_entity=satb1fac.hub_entity)


class TestMontrekExampleBCreate(MontrekCreateViewTestCase):
    viewname = "montrek_example_b_create"
    view_class = me_views.MontrekExampleBCreate

    def build_factories(self):
        self.satd_1 = me_factories.SatD1Factory.create(
            field_d1_str="test1",
        )

        self.satd_2 = me_factories.SatD1Factory.create(
            field_d1_str="test2",
        )

    def creation_data(self):
        return {
            "field_b1_str": "test",
            "field_b1_date": "2024-02-17",
            "field_b2_str": "test2",
            "field_b2_choice": "CHOICE2",
            "link_hub_b_hub_d": [
                self.satd_1.hub_entity.get_hub_value_date().id,
                self.satd_2.hub_entity.get_hub_value_date().id,
            ],
            "alert_level": AlertEnum.OK.value.description,
        }

    def additional_assertions(self, created_object):
        self.assertTrue(created_object.field_d1_str in ["test1,test2", "test2,test1"])


class TestMontrekExampleBUpdate(MontrekUpdateViewTestCase):
    viewname = "montrek_example_b_update"
    view_class = me_views.MontrekExampleBUpdate

    def build_factories(self):
        self.sat1 = me_factories.SatB1Factory(field_b1_str="test")
        me_factories.SatB2Factory()
        self.satd1 = me_factories.SatD1Factory.create(field_d1_str="test1")
        self.satd2 = me_factories.SatD1Factory.create(field_d1_str="test2")
        self.sat1.hub_entity.link_hub_b_hub_d.add(self.satd1.hub_entity)
        self.sat1.hub_entity.link_hub_b_hub_d.add(self.satd2.hub_entity)

    def url_kwargs(self) -> dict:
        return {"pk": self.sat1.hub_entity.get_hub_value_date().id}

    def update_data(self) -> dict:
        return {
            "field_b1_str": "test",
            "field_b1_date": "2024-02-17",
            "field_b2_str": "test2",
            "field_b2_choice": "CHOICE2",
            "alert_level": AlertEnum.OK.value.description,
            "link_hub_b_hub_d": [self.satd2.get_hub_value_date().pk],
            "hub_entity_id": self.sat1.hub_entity.id,
        }

    def test_initial_links_in_form(self):
        response = self.client.get(self.url)
        form = response.context["form"]
        self.assertEqual(form.initial["field_b1_str"], "test")
        expected_sats = [
            self.satd1.hub_entity.get_hub_value_date().id,
            self.satd2.hub_entity.get_hub_value_date().id,
        ]
        for sat_id in expected_sats:
            self.assertIn(
                sat_id,
                form["link_hub_b_hub_d"].value(),
            )

    def test_remove_many_to_many_link(self):
        links = LinkHubBHubD.objects.all()
        self.assertEqual(links.count(), 2)
        for link in links:
            self.assertEqual(
                link.state_date_end, timezone.make_aware(timezone.datetime.max)
            )
        repository = HubBRepository()
        satb1 = repository.receive().first()
        self.assertEqual(satb1.field_b1_str, "test")
        self.assertEqual(satb1.hub.link_hub_b_hub_d.count(), 2)
        self.assertEqual(satb1.field_d1_str, "test1,test2")
        response = self.client.post(self.url, data=self.update_data())
        self.assertRedirects(response, reverse("montrek_example_b_list"))
        links = LinkHubBHubD.objects.all()
        self.assertEqual(links.count(), 2)
        self.assertEqual(
            links[0].state_date_end, timezone.make_aware(timezone.datetime.max)
        )
        self.assertLess(
            links[1].state_date_end, timezone.make_aware(timezone.datetime.max)
        )
        satb1 = repository.receive().get(pk=satb1.pk)
        self.assertEqual(satb1.field_b1_str, "test")
        self.assertEqual(satb1.hub.link_hub_b_hub_d.count(), 2)
        self.assertEqual(satb1.field_d1_str, "test2")

    def test_remove_all_many_to_many_links(self):
        links = LinkHubBHubD.objects.all()
        self.assertEqual(links.count(), 2)
        for link in links:
            self.assertEqual(
                link.state_date_end, timezone.make_aware(timezone.datetime.max)
            )
        repository = HubBRepository()
        satb1 = repository.receive().first()
        self.assertEqual(satb1.field_b1_str, "test")
        self.assertEqual(satb1.hub.link_hub_b_hub_d.count(), 2)
        self.assertEqual(satb1.field_d1_str, "test1,test2")
        update_data = self.update_data()
        update_data["link_hub_b_hub_d"] = []
        response = self.client.post(self.url, data=update_data)
        self.assertRedirects(response, reverse("montrek_example_b_list"))
        links = LinkHubBHubD.objects.all()
        self.assertEqual(links.count(), 2)
        self.assertLess(
            links[0].state_date_end, timezone.make_aware(timezone.datetime.max)
        )
        self.assertLess(
            links[1].state_date_end, timezone.make_aware(timezone.datetime.max)
        )
        satb1 = repository.receive().get(pk=satb1.pk)
        self.assertEqual(satb1.field_b1_str, "test")
        self.assertEqual(satb1.hub.link_hub_b_hub_d.count(), 2)
        self.assertEqual(satb1.field_d1_str, None)


class TestMontrekExampleBReportView(MontrekReportViewTestCase):
    expected_number_of_report_elements = 3
    viewname = "montrek_example_b_report"
    view_class = me_views.MontrekExampleBReport

    def build_factories(self):
        self.sat_b1 = me_factories.SatB1Factory(field_b1_str="test")

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_b1.get_hub_value_date().id}


class TestMontrekExampleBReportFieldEditView(MontrekReportFieldEditViewTestCase):
    viewname = "montrek_example_b_edit_field"
    view_class = me_views.MontrekExampleBReportFieldEditView
    update_field = "field_b1_str"
    updated_content = "Updated Field"

    def build_factories(self):
        self.sat_b1 = me_factories.SatB1Factory(field_b1_str="test")

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_b1.get_hub_value_date().id}


class TestMontrekExampleCListView(MontrekListViewTestCase):
    viewname = "montrek_example_c_list"
    view_class = me_views.MontrekExampleCList
    expected_no_of_rows = 1

    def build_factories(self):
        sat_ts = me_factories.SatTSC2Factory(value_date=datetime.date.today())
        me_factories.SatC1Factory(hub_entity=sat_ts.hub_value_date.hub)


class TestMontrekExampleCCreate(MontrekCreateViewTestCase):
    viewname = "montrek_example_c_create"
    view_class = me_views.MontrekExampleCCreate

    def creation_data(self):
        return {
            "field_c1_str": "test",
            "field_c1_bool": True,
            "field_tsc2_float": 2.0,
            "field_tsc3_int": 2,
            "field_tsc3_str": "testsmest",
            "value_date": "2024-02-17",
        }


class TestMontrekExampleDListView(MontrekListViewTestCase):
    viewname = "montrek_example_d_list"
    view_class = me_views.MontrekExampleDList
    expected_no_of_rows = 1

    def build_factories(self):
        me_factories.SatD1Factory.create(field_d1_str="0", field_d1_int=0)

    def test_file_upload_is_shown(self):
        self.assertTrue(self.response.context["do_simple_file_upload"])
        upload_form = self.response.content
        soup = BeautifulSoup(upload_form, "html.parser")
        with self.subTest("test_attributes"):
            form = soup.find("form")
            self.assertIsNotNone(form)
            form = cast(Tag, form)

            self.assertEqual(form.get("method"), "post")
            self.assertEqual(form.get("enctype"), "multipart/form-data")

        with self.subTest("test_file_input"):
            file_input = soup.find("input", {"type": "file"})
            self.assertIsNotNone(file_input)
            file_input = cast(Tag, file_input)

            self.assertEqual(file_input.get("name"), "file")
            self.assertEqual(file_input.get("id"), "id_upload__file")
            self.assertIn(".xlsx", file_input.get("accept"))
            self.assertIn(".csv", file_input.get("accept"))
            self.assertTrue(file_input.has_attr("required"))

        with self.subTest("test_overwrite_checkbox"):
            checkbox = soup.find("input", {"type": "checkbox"})
            self.assertIsNotNone(checkbox)

            self.assertEqual(checkbox.get("name"), "overwrite")
            self.assertEqual(checkbox.get("id"), "id_upload__overwrite")

        with self.subTest("test_labels_are_bound"):
            file_label = soup.find("label", {"for": "id_upload__file"})
            overwrite_label = soup.find("label", {"for": "id_upload__overwrite"})

            self.assertIsNotNone(file_label)
            self.assertIsNotNone(overwrite_label)

            self.assertEqual(file_label.text.strip(), "File:")
            self.assertEqual(overwrite_label.text.strip(), "Overwrite existing data:")
        with self.subTest("test_submit_button"):
            submit = soup.find("input", {"type": "submit"})
            self.assertIsNotNone(submit)

            self.assertEqual(submit.get("value"), "Upload")
            self.assertIn("input-custom", submit.get("class", []))

    def test_simple_file_upload_csv(self):
        test_file_path = os.path.join(os.path.dirname(__file__), "data", "d_file.csv")
        with open(test_file_path, "rb") as f:
            data = {"file": f}
            self.client.post(self.url, data, follow=True)
        queyset = HubDRepository().receive()
        self.assertEqual(len(queyset), 4)
        registry = FileUploadRegistryRepository().receive().last()
        self.assertEqual(registry.upload_status, "processed")

    def test_simple_file_upload_excel(self):
        test_file_path = os.path.join(os.path.dirname(__file__), "data", "d_file.xlsx")
        with open(test_file_path, "rb") as f:
            data = {"file": f}
            self.client.post(self.url, data, follow=True)
        queyset = HubDRepository().receive()
        self.assertEqual(len(queyset), 4)
        registry = FileUploadRegistryRepository().receive().last()
        self.assertEqual(registry.upload_status, "processed")

    def test_simple_file_upload_unknown(self):
        test_file_path = os.path.join(os.path.dirname(__file__), "data", "d_file.unkwn")
        with open(test_file_path, "rb") as f:
            data = {"file": f}
            self.client.post(self.url, data, follow=True)
        queyset = HubDRepository().receive()
        self.assertEqual(len(queyset), 1)
        registries = FileUploadRegistryRepository().receive()
        self.assertEqual(len(registries), 0)

    @override_settings(IS_TEST_RUN=False)
    def test_simple_file_upload_failure(self):
        test_file_path = os.path.join(
            os.path.dirname(__file__), "data", "d_file_fail.csv"
        )
        with open(test_file_path, "rb") as f:
            data = {"file": f}
            self.client.post(self.url, data, follow=True)
        queyset = HubDRepository().receive()
        self.assertEqual(len(queyset), 1)
        registry = FileUploadRegistryRepository().receive().last()
        self.assertEqual(registry.upload_status, "failed")

    @override_settings(IS_TEST_RUN=False)
    def test_simple_file_upload_overwrite(self):
        # helper methods
        def _write_temporary_file_and_upload(csv_data: str):
            with TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, "upload_file.csv")
                with open(file_path, "w") as f:
                    f.write(csv_data)
                with open(file_path, "rb") as f:
                    csv_data = {"file": f, "overwrite": True}
                    self.client.post(self.url, csv_data, follow=True)

        def _assert_database_values(expected_values):
            queryset = HubDRepository().receive()
            actual_values = queryset.values_list("field_d1_str", "field_d1_int")
            self.assertEqual(list(actual_values), expected_values)

        # upload first file, overwrite factory generated data
        upload_csv_data = dedent(
            """
            D1 String,D1 Int
            a,1
            b,2
            c,3
            """
        )
        _write_temporary_file_and_upload(upload_csv_data)
        expected_values = [("a", 1), ("b", 2), ("c", 3)]
        _assert_database_values(expected_values)

        # upload second file, overwrite first file data
        upload_csv_data = dedent(
            """
            D1 String,D1 Int
            a,1
            b,20
            d,30
            e,40
            """
        )
        _write_temporary_file_and_upload(upload_csv_data)
        expected_values = [("a", 1), ("b", 20), ("d", 30), ("e", 40)]
        _assert_database_values(expected_values)

        # upload the third file which will lead to an error during insertion,
        # the data in the database should not have been deleted
        upload_csv_data = dedent(
            """
            D1 Int
            a
            """
        )
        _write_temporary_file_and_upload(upload_csv_data)
        _assert_database_values(expected_values)


class TestMontrekExampleDCreate(MontrekCreateViewTestCase):
    viewname = "montrek_example_d_create"
    view_class = me_views.MontrekExampleDCreate

    def required_user_permissions(self) -> list[Permission]:
        return [Permission.objects.get(codename="add_hubd")]

    def creation_data(self):
        return {
            "field_d1_str": "test",
            "field_d1_int": 13,
            "value_date": "2024-02-17",
            "field_tsd2_float": 1.0,
            "field_tsd2_int": 2,
        }


class TestMontrekExampleDDelete(MontrekDeleteViewTestCase):
    viewname = "montrek_example_d_delete"
    view_class = me_views.MontrekExampleDDelete

    def build_factories(self):
        self.sattsd2 = me_factories.SatTSD2Factory()
        me_factories.SatD1Factory(hub_entity=self.sattsd2.hub_value_date.hub)

    def url_kwargs(self) -> dict:
        return {"pk": self.sattsd2.hub_value_date.id}


class TestMontrekExampleA1UploadFileView(TransactionTestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)
        self.url = reverse("a1_upload_file")
        self.test_file_path = os.path.join(
            os.path.dirname(__file__), "data", "a_file.csv"
        )
        self.registry_repo = HubAFileUploadRegistryRepository({})

    def test_view_return_correct_html(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "upload_form.html")

    def test_view_post_success(self):
        me_factories.SatA1FieldMapStaticSatelliteFactory(
            source_field="source_field_0",
            database_field="field_a1_str",
            function_name="append_source_field_1",
        )
        me_factories.SatA1FieldMapStaticSatelliteFactory(
            source_field="source_field_1",
            database_field="field_a1_int",
            function_name="multiply_by_value",
            function_parameters={"value": 1000},
        )

        with open(self.test_file_path, "rb") as f:
            data = {"file": f}
            response = self.client.post(self.url, data, follow=True)

        messages = list(response.context["messages"])

        a_hubs = HubARepository().receive()

        self.assertRedirects(response, reverse("a1_view_uploads"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            TASK_SCHEDULED_MESSAGE,
        )

        self.assertEqual(len(a_hubs), 3)

        self.assertEqual(a_hubs[0].field_a1_str, "a1")
        self.assertEqual(a_hubs[1].field_a1_str, "b2")
        self.assertEqual(a_hubs[2].field_a1_str, "c3")

        self.assertEqual(a_hubs[0].field_a1_int, 1000)
        self.assertEqual(a_hubs[1].field_a1_int, 2000)
        self.assertEqual(a_hubs[2].field_a1_int, 3000)
        upload_registry = self.registry_repo.receive().last()
        log_file = upload_registry.log_file
        self.assertTrue(log_file)

    @override_settings(IS_TEST_RUN=False)
    def test_view_post_field_map_exception(self):
        me_factories.SatA1FieldMapStaticSatelliteFactory(
            source_field="source_field_0",
            database_field="field_a1_str",
            function_name="multiply_by_value",
            function_parameters={"value": "a"},
        )
        me_factories.SatA1FieldMapStaticSatelliteFactory(
            source_field="source_field_1",
            database_field="field_a1_int",
            function_name="multiply_by_value",
        )

        with open(self.test_file_path, "rb") as f:
            data = {"file": f}
            response = self.client.post(self.url, data, follow=True)

        messages = list(response.context["messages"])
        upload_registry = self.registry_repo.receive().last()

        a_hubs = HubARepository().receive()

        self.assertRedirects(response, reverse("a1_view_uploads"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            TASK_SCHEDULED_MESSAGE,
        )
        self.assertEqual(upload_registry.upload_status, "failed")
        self.assertEqual(
            upload_registry.upload_message,
            (
                "Errors raised during field mapping:"
                "<br>('source_field_0', 'field_a1_str', 'multiply_by_value', {{'value': 'a'}}, \"TypeError: can't multiply sequence by non-int of type 'str'\")"
                "<br>('source_field_1', 'field_a1_int', 'multiply_by_value', {{}}, \"TypeError: FieldMapFunctionManager.multiply_by_value() missing 1 required positional argument: 'value'\")"
            ),
        )

        self.assertEqual(len(a_hubs), 0)

    @override_settings(IS_TEST_RUN=False)
    def test_view_post_db_creator_exception(self):
        me_factories.SatA1FieldMapStaticSatelliteFactory(
            source_field="source_field_0",
            database_field="field_a1_int",
            function_name="multiply_by_value",
            function_parameters={"value": 10},
        )

        with open(self.test_file_path, "rb") as f:
            data = {"file": f}
            response = self.client.post(self.url, data, follow=True)

        messages = list(response.context["messages"])
        upload_registry = self.registry_repo.receive().last()

        HubARepository().receive()

        self.assertRedirects(response, reverse("a1_view_uploads"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            TASK_SCHEDULED_MESSAGE,
        )
        self.assertEqual(upload_registry.upload_status, "failed")
        self.assertEqual(
            upload_registry.upload_message,
            "Error raised during object creation: <br>ValueError: Field 'field_a1_int' expected a number but got 'aaaaaaaaaa'.",
        )

    def test_unallowed_database_field_in_field_map(self):
        # foo is not available in the target repository and should raise an
        # error
        me_factories.SatA1FieldMapStaticSatelliteFactory(
            source_field="source_field_0",
            database_field="not_in_repository_field_0",
        )
        # bar is an intermediate field and should not raise an error
        me_factories.SatA1FieldMapStaticSatelliteFactory(
            source_field="source_field_1",
            database_field="intermediate_field",
        )
        me_factories.SatA1FieldMapStaticSatelliteFactory(
            source_field="intermediate_field",
            database_field="not_in_repository_field_1",
        )
        # whitelisted fields should not raise an error
        me_factories.SatA1FieldMapStaticSatelliteFactory(
            source_field="source_field_2",
            database_field="whitelisted_field",
        )
        # make sure a map where source and target are the same is not falsely
        # ignored as an intermediate field
        me_factories.SatA1FieldMapStaticSatelliteFactory(
            source_field="not_in_repository_field_2",
            database_field="not_in_repository_field_2",
        )
        with open(self.test_file_path, "rb") as f:
            data = {"file": f}
            response = self.client.post(self.url, data, follow=True)
        registries = self.registry_repo.receive()
        self.assertEqual(registries.count(), 1)
        registry = registries.first()
        messages = list(response.context["messages"])
        a_hubs = HubARepository().receive()
        self.assertRedirects(response, reverse("a1_view_uploads"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            TASK_SCHEDULED_MESSAGE,
        )
        self.assertEqual(registry.upload_status, "failed")
        self.assertEqual(
            registry.upload_message,
            "The following database fields are defined in the field map but are not in the target repository: not_in_repository_field_0, not_in_repository_field_1, not_in_repository_field_2",
        )
        self.assertEqual(len(a_hubs), 0)


class TestMontrekExampleA1UploadHistoryView(MontrekViewTestCase):
    viewname = "a1_file_upload_history"
    view_class = me_views.MontrekExampleA1UploadHistoryView

    def build_factories(self):
        self.user1 = MontrekUserFactory()
        self.user2 = MontrekUserFactory()
        self.huba = me_factories.HubAFileUploadRegistryHubFactory()
        me_factories.HubAFileUploadRegistryStaticSatelliteFactory.create(
            hub_entity=self.huba,
            state_date_end=montrek_time(2024, 2, 17),
            created_by=self.user1,
            comment="initial comment",
        )
        me_factories.HubAFileUploadRegistryStaticSatelliteFactory.create(
            hub_entity=self.huba,
            state_date_start=montrek_time(2024, 2, 17),
            state_date_end=montrek_time(2024, 3, 17),
            created_by=self.user2,
            comment="change comment",
        )
        me_factories.HubAFileUploadRegistryStaticSatelliteFactory.create(
            state_date_start=montrek_time(2024, 3, 17),
            hub_entity=self.huba,
            created_by=self.user2,
            comment="another comment",
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.huba.get_hub_value_date().pk}

    def test_view_with_history_data(self):
        test_history_data_tables = self.response.context_data["history_data_tables"]
        self.assertEqual(len(test_history_data_tables), 3)
        sat_a1_queryset = test_history_data_tables[0].queryset
        self.assertEqual(len(sat_a1_queryset), 3)
        self.assertEqual(sat_a1_queryset[2].comment, "initial comment")
        self.assertEqual(sat_a1_queryset[1].comment, "change comment")
        self.assertEqual(sat_a1_queryset[0].comment, "another comment")

        self.assertEqual(sat_a1_queryset[2].changed_by, self.user1.email)
        self.assertEqual(sat_a1_queryset[1].changed_by, self.user2.email)
        self.assertEqual(sat_a1_queryset[0].changed_by, self.user2.email)


class TestMontrekA1RepositoryDownloadView(MontrekFileResponseTestCase):
    viewname = "a1_download_file"
    view_class = me_views.MontrekExampleA1DownloadFileView
    is_redirected = True

    def build_factories(self):
        self.reg_factory = (
            me_factories.HubAFileUploadRegistryStaticSatelliteFactory.create(
                generate_file_upload_file=True
            )
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.reg_factory.hub_entity.pk}

    def test_return_file(self):
        content = b"".join(self.response.streaming_content)
        self.assertEqual(content, b"test")


class TestMontrekA1RepositoryDownloadLogView(MontrekFileResponseTestCase):
    viewname = "a1_download_log_file"
    view_class = me_views.MontrekExampleA1DownloadFileView
    is_redirected = True

    def build_factories(self):
        self.reg_factory = (
            me_factories.HubAFileUploadRegistryStaticSatelliteFactory.create(
                generate_file_log_file=True
            )
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.reg_factory.hub_entity.pk}

    def test_return_file(self):
        content = b"".join(self.response.streaming_content)
        self.assertEqual(content, b"test")


class TestMontrekExampleA1UploadView(MontrekListViewTestCase):
    viewname = "a1_view_uploads"
    view_class = me_views.MontrekExampleA1UploadView
    expected_no_of_rows = 3

    def build_factories(self):
        self.hub_a = me_factories.HubAFactory.create()
        me_factories.HubAFileUploadRegistryStaticSatelliteFactory.create_batch(3)


class TestRevokeExampleA1UploadTask(TestCase):
    def setUp(self):
        self.previous_url = "http://127.0.0.1:8002/montrek_example/a1_view_uploads"

    @add_logged_in_user
    @patch("file_upload.views.celery_app.control.revoke")
    def test_revoke_file_upload_task(self, mock_revoke):
        registries = (
            me_factories.HubAFileUploadRegistryStaticSatelliteFactory.create_batch(3)
        )
        url = reverse(
            "revoke_file_upload_task", kwargs={"task_id": registries[0].celery_task_id}
        )
        self.client.get(url, HTTP_REFERER=self.previous_url)
        revoked_registry = (
            HubAFileUploadRegistryRepository()
            .receive()
            .get(pk=registries[0].get_hub_value_date().pk)
        )
        self.assertEqual(revoked_registry.upload_status, "revoked")
        self.assertEqual(revoked_registry.upload_message, "Task has been revoked")

    @add_logged_in_user
    @patch("file_upload.views.celery_app.control.revoke")
    def test_revoke_calls_celery(self, mock_revoke):
        # Patch celery task revoke, since we cannot spin up a worker in test environment
        registry = me_factories.HubAFileUploadRegistryStaticSatelliteFactory()
        url = reverse(
            "revoke_file_upload_task", kwargs={"task_id": registry.celery_task_id}
        )
        response = self.client.get(
            url,
            HTTP_REFERER=self.previous_url,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.previous_url)

        mock_revoke.assert_called_once_with(registry.celery_task_id, terminate=True)

    @patch("file_upload.views.celery_app.control.revoke")
    @add_logged_in_user
    def test_revoke_broker_down(self, mock_revoke):
        from kombu.exceptions import OperationalError

        mock_revoke.side_effect = OperationalError("down")

        registry = me_factories.HubAFileUploadRegistryStaticSatelliteFactory()
        url = reverse(
            "revoke_file_upload_task", kwargs={"task_id": registry.celery_task_id}
        )

        response = self.client.get(url, HTTP_REFERER=self.previous_url, follow=True)

        messages_list = list(response.context["messages"])
        self.assertIn("down", str(messages_list[-1]))

    @add_logged_in_user
    @patch("file_upload.views.celery_app.control.revoke")
    def test_revoke_withouut_http_referer(self, mock_revoke):
        url = reverse("revoke_file_upload_task", kwargs={"task_id": "1234"})
        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/home")


class TestMontrekExampleA1FieldMapCreateView(MontrekCreateViewTestCase):
    viewname = "montrek_example_a1_field_map_create"
    view_class = me_views.MontrekExampleA1FieldMapCreateView

    def creation_data(self):
        return {
            "source_field": "source_field_1",
            "database_field": "field_a1_str",
            "step": 1,
            "function_name": "append_source_field_1",
            "function_parameters": "",
        }

    def test_form_function_name_choices(self):
        response = self.client.get(self.url)
        form = response.context["form"]
        self.assertEqual(
            form.fields["function_name"].choices,
            [
                ("append_source_field_1", "append_source_field_1"),
                ("extract_number", "extract_number"),
                ("multiply_by_value", "multiply_by_value"),
                ("no_change", "no_change"),
            ],
        )
        self.assertEqual(form.initial["function_name"], "no_change")

    def test_form_invalid_json(self):
        creation_data = self.creation_data()
        invalid_json_strings = ("abc", "{'a': 'b'}", "{1: 2}", "als;djf}")
        for invalid_json in invalid_json_strings:
            creation_data["function_parameters"] = invalid_json
            response = self.client.post(self.url, creation_data)
            messages = list(response.context["messages"])
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(messages), 1)
            message = str(messages[0])
            self.assertEqual(message, "function_parameters: Enter a valid JSON.")


class TestMontrekExampleA1FieldMapUpdateView(MontrekCreateViewTestCase):
    viewname = "montrek_example_a1_field_map_update"
    view_class = me_views.MontrekExampleA1FieldMapUpdateView

    def build_factories(self):
        self.field_map_factory = (
            me_factories.SatA1FieldMapStaticSatelliteFactory.create(
                source_field="source_field_1",
                database_field="field_a1_str",
            )
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.field_map_factory.get_hub_value_date().pk}

    def creation_data(self):
        return {
            "source_field": "source_field_2",
            "database_field": "field_a1_str",
            "step": 1,
            "function_name": "append_source_field_1",
            "function_parameters": "",
            "hub_entity_id": self.field_map_factory.hub_entity.id,
        }


class TestMontrekExampleA1FieldMapDeleteView(MontrekDeleteViewTestCase):
    viewname = "montrek_example_a1_field_map_delete"
    view_class = me_views.MontrekExampleA1FieldMapDeleteView

    def build_factories(self):
        self.field_map_factory = (
            me_factories.SatA1FieldMapStaticSatelliteFactory.create()
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.field_map_factory.get_hub_value_date().pk}


class TestMontrekExampleA1FieldMapListView(MontrekListViewTestCase):
    viewname = "montrek_example_a1_field_map_list"
    view_class = me_views.MontrekExampleA1FieldMapListView
    expected_no_of_rows = 10

    def build_factories(self):
        me_factories.SatA1FieldMapStaticSatelliteFactory.create_batch(10)


class TestMontrekExampleHubAApiUploadView(MontrekListViewTestCase):
    viewname = "hub_a_view_api_uploads"
    view_class = me_views.MontrekExampleHubAApiUploadView
    expected_no_of_rows = 3

    def build_factories(self):
        me_factories.LinkHubAApiUploadRegistryFactory.create_batch(3)


class TestRunExampleSequentialTask(TestCase):
    def test_run(self):
        url = reverse("run_example_sequential_task")
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)


class TestRunExampleParallelTask(TestCase):
    def test_run(self):
        url = reverse("run_example_parallel_task")
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)


class TestHubARestApiView(MontrekRestApiViewTestCase):
    viewname = "hub_a_rest_api"
    view_class = me_views.HubARestApiView
    expected_no_of_rows = 3

    def build_factories(self):
        hubs = me_factories.HubAFactory.create_batch(3)
        self.sat_a1s = []
        self.sat_a2s = []

        for hub in hubs:
            self.sat_a1s.append(me_factories.SatA1Factory(hub_entity=hub))
            self.sat_a2s.append(me_factories.SatA2Factory(hub_entity=hub))


class TestHubARestApiViewWithFilter(MontrekRestApiViewTestCase):
    viewname = "hub_a_rest_api"
    view_class = me_views.HubARestApiView
    expected_no_of_rows = 1

    def build_factories(self):
        hubs = me_factories.HubAFactory.create_batch(3)
        self.sat_a1s = []
        self.sat_a2s = []

        for i, hub in enumerate(hubs):
            self.sat_a1s.append(
                me_factories.SatA1Factory(hub_entity=hub, field_a1_str=f"field{i}")
            )
            self.sat_a2s.append(me_factories.SatA2Factory(hub_entity=hub))

    def query_params(self) -> dict:
        return {
            "filter_field": "field_a1_str",
            "filter_value": "field1",
            "filter_negate": "False",
            "filter_lookup": "exact",
        }

    def expected_json(self) -> list:
        expected_json = [
            {
                "field_a1_str": self.sat_a1s[1].field_a1_str,
                "field_a1_int": self.sat_a1s[1].field_a1_int,
                "field_a2_str": self.sat_a2s[1].field_a2_str,
                "field_a2_float": self.sat_a2s[1].field_a2_float,
                "field_b1_str": None,
                "individual_field": 0.0,
            }
        ]
        return expected_json


class TestHubBRestApiView(MontrekRestApiViewTestCase):
    viewname = "hub_b_rest_api"
    view_class = me_views.HubBRestApiView

    def build_factories(self):
        hubs = me_factories.HubBFactory.create_batch(3)
        self.sat_b1s = []
        self.sat_b2s = []
        for hub in hubs:
            self.sat_b1s.append(me_factories.SatB1Factory(hub_entity=hub))
            self.sat_b2s.append(me_factories.SatB2Factory(hub_entity=hub))
            satd = me_factories.SatD1Factory.create(field_d1_str="bla")
            hub.link_hub_b_hub_d.add(satd.hub_entity)
            satd = me_factories.SatD1Factory.create(field_d1_str="blubb")
            hub.link_hub_b_hub_d.add(satd.hub_entity)


class TestHubARedirectView(MontrekRedirectViewTestCase):
    viewname = "hub_a_redirect"
    view_class = me_views.HubARedirectView

    def build_factories(self):
        self.hub = me_factories.HubAFactory.create()

    def url_kwargs(self) -> dict:
        return {"pk": self.hub.pk}

    def expected_url(self) -> str:
        return reverse("montrek_example_a_list")


class TestA2ApiUploadView(MontrekViewTestCase):
    view_class = me_views.A2ApiUploadView
    viewname = "do_a2_upload"

    @mock_external_get()
    def test_post(self, mocked_get):
        response = self.client.post(
            self.url, data={"user": "user", "password": "password"}
        )
        self.assertRedirects(response, reverse("hub_a_view_api_uploads"))
        mocked_get.assert_called()

    def test_post__no_user(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post__no_password(self):
        response = self.client.post(self.url, data={"user": "user"})
        self.assertEqual(response.status_code, 200)


class TestTableDataWithReferenceDate(MontrekListViewTestCase):
    viewname = "montrek_example_a_list"
    view_class = me_views.MontrekExampleAList
    expected_no_of_rows = 1

    def query_params(self) -> dict:
        return {"reference_date": ["2023-07-15"]}

    def build_factories(self):
        sat_a11 = me_factories.SatA1Factory(
            state_date_end=montrek_time(2023, 7, 10),
            field_a1_int=5,
        )
        me_factories.SatA1Factory(
            hub_entity=sat_a11.hub_entity,
            state_date_start=montrek_time(2023, 7, 10),
            state_date_end=montrek_time(2023, 7, 20),
            field_a1_int=6,
        )
        me_factories.SatA1Factory(
            hub_entity=sat_a11.hub_entity,
            state_date_start=montrek_time(2023, 7, 20),
            field_a1_int=7,
        )
        me_factories.SatA2Factory(
            hub_entity=sat_a11.hub_entity,
            field_a2_float=8.0,
        )
        hub_a12 = me_factories.HubAFactory(state_date_end=montrek_time(2023, 7, 10))
        me_factories.SatA2Factory(
            hub_entity=hub_a12,
            state_date_end=montrek_time(2023, 7, 10),
            field_a2_float=9,
        )

    def test_assign_old_data(self):
        test_object = self.view.object_list[0]
        self.assertEqual(test_object.field_a1_int, 6)

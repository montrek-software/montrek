import os
from tempfile import TemporaryDirectory
from textwrap import dedent

from django.core.paginator import Page

from baseclasses.dataclasses.alert import AlertEnum
from baseclasses.utils import montrek_time
from django.contrib.auth.models import Permission
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from file_upload.managers.file_upload_manager import TASK_SCHEDULED_MESSAGE
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekDeleteViewTestCase,
    MontrekDownloadViewTestCase,
    MontrekFileResponseTestCase,
    MontrekListViewTestCase,
    MontrekRedirectViewTestCase,
    MontrekReportFieldEditViewTestCase,
    MontrekRestApiViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekViewTestCase,
    MontrekReportViewTestCase,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory

from montrek_example import views as me_views
from montrek_example.models import LinkHubBHubD
from montrek_example.repositories.hub_a_repository import (
    HubAFileUploadRegistryRepository,
    HubARepository,
)
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.repositories.hub_d_repository import HubDRepository
from montrek_example.tests.factories import montrek_example_factories as me_factories


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
        self.assertEqual(len(HubARepository().receive()), 2)

        url = reverse(
            "montrek_example_a_list",
        )
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

        response = self.client.get(url, data={"reset_filter": "true"}, follow=True)
        obj_list = response.context_data["object_list"]
        self.assertRedirects(response, url)
        self.assertEqual(len(obj_list), 2)


class TestMontrekExampleAListViewPages(MontrekListViewTestCase):
    viewname = "montrek_example_a_list"
    view_class = me_views.MontrekExampleAList
    expected_no_of_rows = 10

    def build_factories(self):
        me_factories.SatA2Factory.create_batch(15)

    def test_selected_and_remember_pages(self):
        query_params = {"page": 2}
        response = self.client.get(self.url, data=query_params)
        test_page = response.context_data["object_list"]
        self.assertIsInstance(test_page, Page)
        self.assertEqual(test_page.number, 2)
        response = self.client.get(self.url)
        test_page = response.context_data["object_list"]
        self.assertIsInstance(test_page, Page)
        self.assertEqual(test_page.number, 2)


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


class TestMontrekExampleADownloadView(MontrekDownloadViewTestCase):
    viewname = "montrek_example_a_download"
    view_class = me_views.MontrekExampleADownloadView

    def expected_filename(self) -> str:
        return "example_md.txt"

    def additional_download_assertions(self):
        self.assertEqual(
            self.response.content.decode(),
            "| A1 String   | A1 Int   | A2 String   | A2 Float   | B1 String   |\n|-------------|----------|-------------|------------|-------------|",
        )


class TestMontrekExampleADetailView(MontrekViewTestCase):
    viewname = "montrek_example_a_details"
    view_class = me_views.MontrekExampleADetails

    def build_factories(self):
        hub_vd_0 = me_factories.AHubValueDateFactory(value_date=None)
        me_factories.SatA1Factory(hub_entity=hub_vd_0.hub)
        self.hub_vd = me_factories.AHubValueDateFactory(value_date=None)
        me_factories.SatA1Factory(hub_entity=self.hub_vd.hub)

    def url_kwargs(self) -> dict:
        return {"pk": self.hub_vd.hub.id}


class TestMontrekExampleADelete(MontrekDeleteViewTestCase):
    viewname = "montrek_example_a_delete"
    view_class = me_views.MontrekExampleADelete

    def build_factories(self):
        self.sata1 = me_factories.SatA1Factory()
        me_factories.SatA2Factory(hub_entity=self.sata1.hub_entity)

    def url_kwargs(self) -> dict:
        return {"pk": self.sata1.get_hub_value_date().id}


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
        sat_ts = me_factories.SatTSC2Factory()
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
                "<br>('source_field_0', 'field_a1_str', 'multiply_by_value', {'value': 'a'}, \"TypeError: can't multiply sequence by non-int of type 'str'\")"
                "<br>('source_field_1', 'field_a1_int', 'multiply_by_value', {}, \"TypeError: FieldMapFunctionManager.multiply_by_value() missing 1 required positional argument: 'value'\")"
            ),
        )

        self.assertEqual(len(a_hubs), 0)

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

    def expected_json(self) -> list:
        expected_json = []
        for i in range(3):
            entry = {
                "field_a1_str": self.sat_a1s[i].field_a1_str,
                "field_a1_int": self.sat_a1s[i].field_a1_int,
                "field_a2_str": self.sat_a2s[i].field_a2_str,
                "field_a2_float": self.sat_a2s[i].field_a2_float,
                "field_b1_str": None,
            }
            expected_json.append(entry)
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

    def expected_json(self) -> list:
        expected_json = []
        for i in range(3):
            entry = {
                "field_b1_str": self.sat_b1s[i].field_b1_str,
                "field_b1_date": self.sat_b1s[i].field_b1_date.strftime("%Y-%m-%d"),
                "field_b2_str": self.sat_b2s[i].field_b2_str,
                "field_b2_choice": self.sat_b2s[i].field_b2_choice.value,
                "field_d1_str": "bla",
                "field_d1_int": "0",
                "alert_level": AlertEnum.OK.value.description,
                "alert_message": None,
            }
            expected_json.append(entry)
        return expected_json


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

    def test_post(self):
        response = self.client.post(
            self.url, data={"user": "user", "password": "password"}
        )
        self.assertRedirects(response, reverse("hub_a_view_api_uploads"))

    def test_post__no_user(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post__no_password(self):
        response = self.client.post(self.url, data={"user": "user"})
        self.assertEqual(response.status_code, 200)

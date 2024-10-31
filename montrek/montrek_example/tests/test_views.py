import os

from baseclasses.dataclasses.alert import AlertEnum
from baseclasses.utils import montrek_time
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from file_upload.repositories.file_upload_registry_repository import (
    FileUploadRegistryRepository,
)
from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekDeleteViewTestCase,
    MontrekFileResponseTestCase,
    MontrekListViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekViewTestCase,
    MontrekRestApiViewTestCase,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory

from montrek_example import views as me_views
from montrek_example.repositories.hub_a_repository import (
    HubAFileUploadRegistryRepository,
    HubARepository,
)
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
        self.assertEqual(len(HubARepository().std_queryset()), 2)

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
        self.assertEqual(obj_list[0].id, other_sata1.hub_entity.id)

        # The filter should persist for this path until reset
        response = self.client.get(url)
        obj_list = response.context_data["object_list"]
        self.assertEqual(len(obj_list), 1)
        self.assertEqual(obj_list[0].id, other_sata1.hub_entity.id)

        response = self.client.get(url, data={"reset_filter": "true"}, follow=True)
        obj_list = response.context_data["object_list"]
        self.assertRedirects(response, url)
        self.assertEqual(len(obj_list), 2)


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


class TestMontrekExampleAUpdateView(MontrekUpdateViewTestCase):
    viewname = "montrek_example_a_update"
    view_class = me_views.MontrekExampleAUpdate

    def build_factories(self):
        self.sat_a1 = me_factories.SatA1Factory()
        me_factories.SatA2Factory(hub_entity=self.sat_a1.hub_entity)

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_a1.hub_entity.id}

    def update_data(self):
        return {
            "field_a1_str": "test_update",
            "field_a1_int": 2,
            "field_a2_str": "test2_update",
            "field_a2_float": 3.0,
        }


class TestMontrekExampleAReportView(MontrekViewTestCase):
    viewname = "montrek_example_report"
    view_class = me_views.MontrekExampleReport


class TestMontrekExampleADetailView(MontrekViewTestCase):
    viewname = "montrek_example_a_details"
    view_class = me_views.MontrekExampleADetails

    def build_factories(self):
        self.sat_a = me_factories.SatA1Factory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_a.hub_entity.id}


class TestMontrekExampleADelete(MontrekDeleteViewTestCase):
    viewname = "montrek_example_a_delete"
    view_class = me_views.MontrekExampleADelete

    def build_factories(self):
        self.sat_a1 = me_factories.SatA1Factory()
        me_factories.SatA2Factory(hub_entity=self.sat_a1.hub_entity)

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_a1.hub_entity.id}


class TestMontrekExampleAHistoryView(MontrekViewTestCase):
    viewname = "montrek_example_a_history"
    view_class = me_views.MontrekExampleAHistory

    def build_factories(self):
        self.sat_a = me_factories.SatA1Factory()

    def url_kwargs(self) -> dict:
        return {"pk": self.sat_a.hub_entity.id}

    def test_view_with_history_data(self):
        huba = me_factories.HubAFactory()
        user1 = MontrekUserFactory()
        user2 = MontrekUserFactory()
        me_factories.SatA1Factory(
            hub_entity=huba,
            field_a1_str="TestFeld",
            field_a1_int=5,
            state_date_end=montrek_time(2024, 2, 17),
            created_by=user1,
            comment="initial comment",
        )
        me_factories.SatA1Factory(
            hub_entity=huba,
            field_a1_str="TestFeld",
            field_a1_int=6,
            state_date_start=montrek_time(2024, 2, 17),
            created_by=user2,
            comment="change comment",
        )
        me_factories.SatA2Factory(
            hub_entity=huba,
            field_a2_str="ConstantTestFeld",
            field_a2_float=6.0,
            created_by=user2,
            comment="another comment",
        )
        url = reverse("montrek_example_a_history", kwargs={"pk": huba.id})
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
        self.d_fac1 = me_factories.SatD1Factory.create(
            field_d1_str="test1",
        )
        self.d_fac2 = me_factories.SatD1Factory.create(
            field_d1_str="test2",
        )

    def creation_data(self):
        return {
            "field_b1_str": "test",
            "field_b1_date": "2024-02-17",
            "field_b2_str": "test2",
            "field_b2_choice": "CHOICE2",
            "link_hub_b_hub_d": [self.d_fac1.hub_entity.id, self.d_fac2.hub_entity.id],
            "alert_level": AlertEnum.OK.value.description,
        }

    def additional_assertions(self, created_object):
        self.assertEqual(created_object.field_d1_str, "test1,test2")


class TestMontrekExampleBUpdate(MontrekUpdateViewTestCase):
    viewname = "montrek_example_b_update"
    view_class = me_views.MontrekExampleBUpdate

    def build_factories(self):
        self.satb1 = me_factories.SatB1Factory()
        me_factories.SatB2Factory(hub_entity=self.satb1.hub_entity)

    def url_kwargs(self) -> dict:
        return {"pk": self.satb1.hub_entity.id}

    def update_data(self) -> dict:
        return {
            "field_b1_str": "test",
            "field_b1_date": "2024-02-17",
            "field_b2_str": "test2",
            "field_b2_choice": "CHOICE2",
            "alert_level": AlertEnum.OK.value.description,
        }


class TestMontrekExampleCListView(MontrekListViewTestCase):
    viewname = "montrek_example_c_list"
    view_class = me_views.MontrekExampleCList
    expected_no_of_rows = 1

    def build_factories(self):
        satc1fac = me_factories.SatC1Factory()
        me_factories.SatTSC2Factory(hub_entity=satc1fac.hub_entity)


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
        me_factories.SatD1Factory.create()

    def test_simple_file_upload_csv(self):
        test_file_path = os.path.join(os.path.dirname(__file__), "data", "d_file.csv")
        with open(test_file_path, "rb") as f:
            data = {"file": f}
            self.client.post(self.url, data, follow=True)
        queyset = HubDRepository().std_queryset()
        self.assertEqual(len(queyset), 4)
        registry = FileUploadRegistryRepository().std_queryset().last()
        self.assertEqual(registry.upload_status, "processed")

    def test_simple_file_upload_excel(self):
        test_file_path = os.path.join(os.path.dirname(__file__), "data", "d_file.xlsx")
        with open(test_file_path, "rb") as f:
            data = {"file": f}
            self.client.post(self.url, data, follow=True)
        queyset = HubDRepository().std_queryset()
        self.assertEqual(len(queyset), 4)
        registry = FileUploadRegistryRepository().std_queryset().last()
        self.assertEqual(registry.upload_status, "processed")

    def test_simple_file_upload_unknown(self):
        test_file_path = os.path.join(os.path.dirname(__file__), "data", "d_file.unkwn")
        with open(test_file_path, "rb") as f:
            data = {"file": f}
            self.client.post(self.url, data, follow=True)
        queyset = HubDRepository().std_queryset()
        self.assertEqual(len(queyset), 1)
        registries = FileUploadRegistryRepository().std_queryset()
        self.assertEqual(len(registries), 0)

    def test_simple_file_upload_failure(self):
        test_file_path = os.path.join(
            os.path.dirname(__file__), "data", "d_file_fail.csv"
        )
        with open(test_file_path, "rb") as f:
            data = {"file": f}
            self.client.post(self.url, data, follow=True)
        queyset = HubDRepository().std_queryset()
        self.assertEqual(len(queyset), 1)
        registry = FileUploadRegistryRepository().std_queryset().last()
        self.assertEqual(registry.upload_status, "failed")


class TestMontrekExampleDCreate(MontrekCreateViewTestCase):
    viewname = "montrek_example_d_create"
    view_class = me_views.MontrekExampleDCreate
    user_permissions = ["add_hubd"]

    def creation_data(self):
        return {
            "field_d1_str": "test",
            "field_d1_int": 13,
        }

    def test_view_without_permission(self):
        self.user.user_permissions.remove(self.permission)
        previous_url = reverse("montrek_example_d_list")
        response = self.client.get(self.url, HTTP_REFERER=previous_url, follow=True)
        messages = list(response.context["messages"])
        self.assertRedirects(response, previous_url)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            messages[0].message,
            "You do not have the required permissions to access this page.",
        )


class TestMontrekExampleA1UploadFileView(TransactionTestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)
        self.url = reverse("a1_upload_file")
        self.test_file_path = os.path.join(
            os.path.dirname(__file__), "data", "a_file.csv"
        )

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

        a_hubs = HubARepository().std_queryset()

        self.assertRedirects(response, reverse("a1_view_uploads"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "Successfully uploaded 3 rows.",
        )

        self.assertEqual(len(a_hubs), 3)

        self.assertEqual(a_hubs[0].field_a1_str, "a1")
        self.assertEqual(a_hubs[1].field_a1_str, "b2")
        self.assertEqual(a_hubs[2].field_a1_str, "c3")

        self.assertEqual(a_hubs[0].field_a1_int, 1000)
        self.assertEqual(a_hubs[1].field_a1_int, 2000)
        self.assertEqual(a_hubs[2].field_a1_int, 3000)
        upload_registry = HubAFileUploadRegistryRepository({}).std_queryset().last()
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

        a_hubs = HubARepository().std_queryset()

        self.assertRedirects(response, reverse("a1_view_uploads"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
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

        HubARepository().std_queryset()

        self.assertRedirects(response, reverse("a1_view_uploads"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "Error raised during object creation: <br>ValueError: Field 'field_a1_int' expected a number but got 'aaaaaaaaaa'.",
        )

    def test_unallowed_database_field_in_field_map(self):
        me_factories.SatA1FieldMapStaticSatelliteFactory(
            source_field="source_field_0",
            database_field="foo",
        )
        with open(self.test_file_path, "rb") as f:
            data = {"file": f}
            response = self.client.post(self.url, data, follow=True)
        messages = list(response.context["messages"])
        a_hubs = HubARepository().std_queryset()
        self.assertRedirects(response, reverse("a1_view_uploads"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "The following database fields are defined in the field map but are not in the target repository: foo",
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
        return {"pk": self.huba.pk}

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

    def test_form_database_field_choices(self):
        response = self.client.get(self.url)
        form = response.context["form"]

        self.assertEqual(
            form.fields["database_field"].choices,
            [
                ("comment", "comment"),
                ("field_a1_int", "field_a1_int"),
                ("field_a1_str", "field_a1_str"),
            ],
        )

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
        return {"pk": self.field_map_factory.hub_entity.pk}

    def creation_data(self):
        return {
            "source_field": "source_field_2",
            "database_field": "field_a1_str",
            "step": 1,
            "function_name": "append_source_field_1",
            "function_parameters": "",
        }


class TestMontrekExampleA1FieldMapDeleteView(MontrekDeleteViewTestCase):
    viewname = "montrek_example_a1_field_map_delete"
    view_class = me_views.MontrekExampleA1FieldMapDeleteView

    def build_factories(self):
        self.field_map_factory = (
            me_factories.SatA1FieldMapStaticSatelliteFactory.create()
        )

    def url_kwargs(self) -> dict:
        return {"pk": self.field_map_factory.hub_entity.pk}


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

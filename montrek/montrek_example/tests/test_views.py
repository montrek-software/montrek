import os
from django.test import TransactionTestCase
from django.urls import reverse
from file_upload.tests.factories.field_map_factories import (
    FieldMapStaticSatelliteFactory,
)
from baseclasses.dataclasses.alert import AlertEnum
from file_upload.tests.factories.file_upload_factories import (
    FileUploadRegistryStaticSatelliteFactory,
)
from montrek_example import views as me_views
from testing.test_cases.view_test_cases import (
    MontrekCreateViewTestCase,
    MontrekUpdateViewTestCase,
    MontrekViewTestCase,
    MontrekListViewTestCase,
    MontrekDeleteViewTestCase,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from montrek_example.tests.factories import montrek_example_factories as me_factories
from montrek_example.repositories.hub_a_repository import HubARepository
from baseclasses.utils import montrek_time


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
            "link_hub_b_hub_d": [self.d_fac1.id, self.d_fac2.id],
            "alert_level": AlertEnum.OK.value.description,
        }

    def additional_assertions(self, created_object):
        self.assertEqual(created_object.field_d1_str, "test1,test2")


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
        }


class TestMontrekExampleDListView(MontrekListViewTestCase):
    viewname = "montrek_example_d_list"
    view_class = me_views.MontrekExampleDList
    expected_no_of_rows = 1

    def build_factories(self):
        me_factories.SatD1Factory.create()


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
        FieldMapStaticSatelliteFactory(
            source_field="source_field_0",
            database_field="field_a1_str",
            function_name="append_source_field_1",
        )
        FieldMapStaticSatelliteFactory(
            source_field="source_field_1",
            database_field="field_a1_int",
            function_name="multiply_by_1000",
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

    def test_view_post_field_map_exception(self):
        FieldMapStaticSatelliteFactory(
            source_field="source_field_0",
            database_field="field_a1_str",
            function_name="multiply_by_value",
            function_parameters={"value": "a"},
        )
        FieldMapStaticSatelliteFactory(
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
        FieldMapStaticSatelliteFactory(
            source_field="source_field_0",
            database_field="field_a1_int",
            function_name="multiply_by_value",
            function_parameters={"value": 10},
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
            "Error raised during object creation: <br>ValueError: Field 'field_a1_int' expected a number but got 'aaaaaaaaaa'.",
        )


class TestMontrekExampleA1UploadView(MontrekListViewTestCase):
    viewname = "a1_view_uploads"
    view_class = me_views.MontrekExampleA1UploadView
    expected_no_of_rows = 2

    def build_factories(self):
        self.hub_a = me_factories.HubAFactory.create()
        file_factories = FileUploadRegistryStaticSatelliteFactory.create_batch(3)
        for file_factory in file_factories[:-1]:
            me_factories.LinkHubAFileUploadRegistryFactory.create(
                hub_in=self.hub_a, hub_out=file_factory.hub_entity
            )


class TestMontrekExampleA1FieldMapCreateView(MontrekCreateViewTestCase):
    viewname = "montrek_example_a1_field_map_create"
    view_class = me_views.MontrekExampleA1FieldMapCreateView

    def creation_data(self):
        return {
            "source_field": "source_field_1",
            "database_field": "field_a1_str",
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
                ("multiply_by_1000", "multiply_by_1000"),
                ("multiply_by_value", "multiply_by_value"),
                ("no_change", "no_change"),
            ],
        )
        self.assertEqual(form.initial["function_name"], "no_change")


class TestMontrekExampleA1FieldMapListView(MontrekListViewTestCase):
    viewname = "montrek_example_a1_field_map_list"
    view_class = me_views.MontrekExampleA1FieldMapListView
    expected_no_of_rows = 10

    def build_factories(self):
        FieldMapStaticSatelliteFactory.create_batch(12)


class TestMontrekExampleHubAApiUploadView(MontrekListViewTestCase):
    viewname = "hub_a_view_api_uploads"
    view_class = me_views.MontrekExampleHubAApiUploadView
    expected_no_of_rows = 3

    def build_factories(self):
        me_factories.LinkHubAApiUploadRegistryFactory.create_batch(3)

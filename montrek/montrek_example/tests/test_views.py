import os
import datetime
from django.test import TestCase
from django.urls import reverse
from file_upload.tests.factories.field_map_factories import (
    FieldMapStaticSatelliteFactory,
)
from user.tests.factories.montrek_user_factories import MontrekUserFactory
from montrek_example import views
from montrek_example.tests.factories import montrek_example_factories as me_factories
from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.repositories.hub_c_repository import HubCRepository
from montrek_example.repositories.hub_d_repository import HubDRepository
from baseclasses.utils import montrek_time


class TestMontrekExampleACreateView(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)

    def test_view_return_correct_html(self):
        url = reverse("montrek_example_a_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_create.html")

    def test_view_post_success(self):
        url = reverse("montrek_example_a_create")
        data = {
            "field_a1_str": "test",
            "field_a1_int": 1,
            "field_a2_str": "test2",
            "field_a2_float": 2.0,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        # Check added data
        std_query = HubARepository().std_queryset()
        self.assertEqual(std_query.count(), 1)
        created_object = std_query.first()
        self.assertEqual(created_object.field_a1_str, "test")
        self.assertEqual(created_object.field_a1_int, 1)
        self.assertEqual(created_object.field_a2_str, "test2")
        self.assertEqual(created_object.field_a2_float, 2)


class TestMontrekExampleADetailView(TestCase):
    def test_view_return_correct_html(self):
        sat_a = me_factories.SatA1Factory()
        url = reverse("montrek_example_a_details", kwargs={"pk": sat_a.hub_entity.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_details.html")


class TestMontrekExampleAHistoryView(TestCase):
    def test_view_return_correct_html(self):
        sat_a = me_factories.SatA1Factory()
        url = reverse("montrek_example_a_history", kwargs={"pk": sat_a.hub_entity.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_history.html")

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


class TestMontrekExampleBListView(TestCase):
    def setUp(self):
        satb1fac = me_factories.SatB1Factory()
        me_factories.SatB2Factory(hub_entity=satb1fac.hub_entity)

    def test_view_return_correct_html(self):
        url = reverse("montrek_example_b_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_table.html")
        test_queryset = response.context_data["object_list"].object_list
        self.assertEqual(len(test_queryset), 1)


class TestMontrekExampleBCreate(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)
        self.d_fac1 = me_factories.SatD1Factory.create(
            field_d1_str="test1",
        )
        self.d_fac2 = me_factories.SatD1Factory.create(
            field_d1_str="test2",
        )

    def test_view_return_correct_html(self):
        url = reverse("montrek_example_b_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_create.html")

    def test_view_post_success(self):
        url = reverse("montrek_example_b_create")
        data = {
            "field_b1_str": "test",
            "field_b1_date": "2024-02-17",
            "field_b2_str": "test2",
            "field_b2_choice": "CHOICE2",
            "link_hub_b_hub_d": [self.d_fac1.id, self.d_fac2.id],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        # Check added data
        std_query = HubBRepository().std_queryset()
        self.assertEqual(std_query.count(), 1)
        created_object = std_query.first()
        self.assertEqual(created_object.field_b1_str, "test")
        self.assertEqual(created_object.field_b1_date, datetime.date(2024, 2, 17))
        self.assertEqual(created_object.field_b2_str, "test2")
        self.assertEqual(created_object.field_b2_choice, "CHOICE2")
        # TODO Fix test
        # self.assertEqual(created_object.field_d1_str, "test1, test2")


class TestMontrekExampleCListView(TestCase):
    def setUp(self):
        satc1fac = me_factories.SatC1Factory()
        me_factories.SatTSC2Factory(hub_entity=satc1fac.hub_entity)

    def test_view_return_correct_html(self):
        url = reverse("montrek_example_c_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_table.html")
        test_queryset = response.context_data["object_list"].object_list
        self.assertEqual(len(test_queryset), 1)


class TestMontrelExampleCCreate(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)

    def test_view_return_correct_html(self):
        url = reverse("montrek_example_c_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_create.html")

    def test_view_post_success(self):
        url = reverse("montrek_example_c_create")
        data = {
            "field_c1_str": "test",
            "field_c1_bool": True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        # Check added data
        std_query = HubCRepository().std_queryset()
        self.assertEqual(std_query.count(), 1)
        created_object = std_query.first()
        self.assertEqual(created_object.field_c1_str, "test")
        self.assertEqual(created_object.field_c1_bool, 1)


class TestMontrekExampleDListView(TestCase):
    def setUp(self):
        me_factories.SatD1Factory.create()

    def test_view_return_correct_html(self):
        url = reverse("montrek_example_d_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_table.html")
        test_queryset = response.context_data["object_list"].object_list
        self.assertEqual(len(test_queryset), 1)


class TestMontrekExampleDCreate(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)

    def test_view_return_correct_html(self):
        url = reverse("montrek_example_d_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_create.html")

    def test_view_post_success(self):
        url = reverse("montrek_example_d_create")
        data = {
            "field_d1_str": "test",
            "field_d1_int": 13,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        # Check added data
        std_query = HubDRepository().std_queryset()
        self.assertEqual(std_query.count(), 1)
        created_object = std_query.first()
        self.assertEqual(created_object.field_d1_str, "test")
        self.assertEqual(created_object.field_d1_int, 13)


class TestMontrekExampleA1UploadFileView(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)
        self.url = reverse("a1_upload_file")

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
        test_file_path = os.path.join(os.path.dirname(__file__), "data", "a_file.csv")

        with open(test_file_path, "rb") as f:
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


class TestMontrekExampleA1UploadView(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)
        self.url = reverse("a1_view_uploads")

    def test_view_return_correct_html(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_table.html")


class TestMontrekExampleA1FieldMapCreateView(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)
        self.url = reverse("montrek_example_a1_field_map_create")

    def test_view_return_correct_html(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_create.html")

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
                ("no_change", "no_change"),
            ],
        )
        self.assertEqual(form.initial["function_name"], "no_change")


class TestMontrekExampleA1FieldMapListView(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()
        self.client.force_login(self.user)
        self.url = reverse("montrek_example_a1_field_map_list")

    def test_view_return_correct_html(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_table.html")

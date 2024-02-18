from django.test import TestCase
from django.urls import reverse
from montrek_example import views
from montrek_example.tests.factories import montrek_example_factories as me_factories
from montrek_example.repositories.hub_a_repository import HubARepository
from baseclasses.utils import montrek_time


class TestMontrekExampleACreateView(TestCase):
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


class TestMontrekExampleAHistoryView(TestCase):
    def test_view_return_correct_html(self):
        sat_a = me_factories.SatA1Factory()
        url = reverse("montrek_example_a_history", kwargs={"pk": sat_a.hub_entity.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "montrek_table.html")

    def test_view_with_history_data(self):
        huba = me_factories.HubAFactory()
        me_factories.SatA1Factory(
            hub_entity=huba,
            field_a1_str="TestFeld",
            field_a1_int=5,
            state_date_end=montrek_time(2024, 2, 17),
        )
        me_factories.SatA1Factory(
            hub_entity=huba,
            field_a1_str="TestFeld",
            field_a1_int=6,
            state_date_start=montrek_time(2024, 2, 17),
        )
        me_factories.SatA2Factory(
            hub_entity=huba,
            field_a2_str="ConstantTestFeld",
            field_a2_float=6.0,
        )
        url = reverse("montrek_example_a_history", kwargs={"pk": huba.id})
        response = self.client.get(url)
        test_queryset = response.context_data["object_list"]
        self.assertEqual(test_queryset.count(), 2)
        self.assertEqual(test_queryset[0].field_a1_int, 5)
        self.assertEqual(test_queryset[1].field_a1_int, 6)
        self.assertEqual(test_queryset[0].change_date[:10], "0001-01-01")
        self.assertEqual(test_queryset[1].change_date[:10], "2024-02-17")

        self.assertEqual(test_queryset[0].field_a1_str, test_queryset[1].field_a1_str)
        self.assertEqual(test_queryset[0].field_a2_str, test_queryset[1].field_a2_str)
        self.assertEqual(
            test_queryset[0].field_a2_float, test_queryset[1].field_a2_float
        )

import datetime
from django.test import TestCase
from django.urls import reverse
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
        test_queryset = response.context_data["object_list"].object_list
        self.assertEqual(len(test_queryset), 2)
        self.assertEqual(test_queryset[1].field_a1_int, 5)
        self.assertEqual(test_queryset[0].field_a1_int, 6)
        self.assertEqual(test_queryset[1].change_date[:10], "0001-01-01")
        self.assertEqual(test_queryset[0].change_date[:10], "2024-02-17")
        self.assertEqual(test_queryset[0].change_comment, "change comment")
        self.assertEqual(
            test_queryset[1].change_comment, "initial comment,another comment"
        )

        self.assertEqual(test_queryset[0].field_a1_str, test_queryset[1].field_a1_str)
        self.assertEqual(test_queryset[0].field_a2_str, test_queryset[1].field_a2_str)
        self.assertEqual(
            test_queryset[0].field_a2_float, test_queryset[1].field_a2_float
        )
        self.assertEqual(test_queryset[0].changed_by, user2.email)
        self.assertEqual(test_queryset[1].changed_by, f"{user1.email},{user2.email}")


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


class TestMontrelExampleDCreate(TestCase):
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

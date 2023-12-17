from django.test import TestCase
from django.urls import reverse
from montrek_example import views
from montrek_example.repositories.hub_a_repository import HubARepository

class TestMontrekExampleACreateView(TestCase):
    def test_view_return_correct_html(self):
        url = reverse('montrek_example_a_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'montrek_create.html')

    def test_view_post_success(self):
        url = reverse('montrek_example_a_create')
        data = {'field_a1_str': 'test',
                'field_a1_int': 1,
                'field_a2_str': 'test2',
                'field_a2_float': 2}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        # Check added data
        std_query = HubARepository(None).std_queryset()
        self.assertEqual(std_query.count(), 1)
        created_object = std_query.first()
        self.assertEqual(created_object.field_a1_str, 'test')
        self.assertEqual(created_object.field_a1_int, 1)
        self.assertEqual(created_object.field_a2_str, 'test2')
        self.assertEqual(created_object.field_a2_float, 2)



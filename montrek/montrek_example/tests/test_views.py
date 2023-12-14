from django.test import TestCase
from montrek_example import views

class TestMontrekExampleACreateView(TestCase):
    def test_view_return_correct_html(self):
        response = self.client.get('/montrek_example/a/create/')
        self.assertTemplateUsed(response, 'montrek_create.html')

    def test_view_class(self):
        test_view = views.MontrekExampleACreate()

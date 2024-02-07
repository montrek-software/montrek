from django.test import TestCase
from django.urls import reverse


class TestAssetCreateView(TestCase):
    def test_asset_create_returns_correct_html(self):
        url = reverse("country_create")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "montrek_create.html")

from django.test import TestCase
from django.urls import reverse

from asset import views as asset_views

class TestAssetOverview(TestCase):
    def test_asset_overview_returns_correct_html(self):
        url = reverse('asset')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'montrek_table.html')

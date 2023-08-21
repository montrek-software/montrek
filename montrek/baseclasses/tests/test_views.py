from django.test import TestCase


class TestUnderConstruction(TestCase):
    def test_under_construction(self):
        response = self.client.get("/under_construction")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "under_construction.html")

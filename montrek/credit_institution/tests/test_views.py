from django.test import TestCase
from credit_institution.views import CreditInstitutionOverview
from credit_institution.tests.factories.credit_institution_factories import CreditInstitutionStaticSatelliteFactory

class TestCreditInstitutionOverview(TestCase):
    def test_get(self):
        response = self.client.get('/credit_institution/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'montrek_table.html')

class TestCreditInstitutionDetailView(TestCase):
    def setUp(self):
        self.credit_institution = CreditInstitutionStaticSatelliteFactory.create()

    def test_get(self):
        response = self.client.get(f'/credit_institution/{self.credit_institution.hub_entity.id}/details')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'montrek_details.html')

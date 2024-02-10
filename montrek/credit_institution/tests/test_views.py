from django.test import TestCase
from credit_institution.tests.factories.credit_institution_factories import CreditInstitutionStaticSatelliteFactory
from country.tests.factories.country_factories import  CountryStaticSatelliteFactory

class TestCreditInstitutionOverview(TestCase):
    def test_get(self):
        response = self.client.get('/credit_institution/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'montrek_table.html')

class TestCreditInstitutionDetailView(TestCase):
    def setUp(self):
        self.credit_institution = CreditInstitutionStaticSatelliteFactory.create()
        country = CountryStaticSatelliteFactory.create()
        self.credit_institution.hub_entity.link_credit_institution_country.add(country.hub_entity)

    def test_get(self):
        response = self.client.get(f'/credit_institution/{self.credit_institution.hub_entity.id}/details')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'montrek_details.html')

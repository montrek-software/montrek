from django.test import TestCase
from credit_institution.tests.factories.credit_institution_factories import CreditInstitutionHubFactory
from credit_institution.tests.factories.credit_institution_factories import CreditInstitutionStaticSatelliteFactory
from credit_institution.models import CreditInstitutionStaticSatellite

class TestCreditInstitutionModels(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hub = CreditInstitutionHubFactory()
        cls.satellite = CreditInstitutionStaticSatelliteFactory(hub_entity=cls.hub)

    def test_credit_institution_static_satellite_attrs(self):
        credit_institutions = CreditInstitutionStaticSatellite.objects.all()
        self.assertEqual(credit_institutions.count(), 1)
        self.assertTrue(isinstance(credit_institutions.first().credit_institution_name,
                                   str))

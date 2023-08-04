import hashlib
from django.test import TestCase
from credit_institution.tests.factories.credit_institution_factories import (
    CreditInstitutionHubFactory,
)
from credit_institution.tests.factories.credit_institution_factories import (
    CreditInstitutionStaticSatelliteFactory,
)
from credit_institution.models import CreditInstitutionStaticSatellite


class TestCreditInstitutionModels(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hub = CreditInstitutionHubFactory()
        cls.satellite = CreditInstitutionStaticSatelliteFactory(hub_entity=cls.hub)

    def test_credit_institution_static_satellite_attrs(self):
        credit_institutions = CreditInstitutionStaticSatellite.objects.all()
        self.assertEqual(credit_institutions.count(), 1)
        self.assertTrue(
            isinstance(credit_institutions.first().credit_institution_name, str)
        )

    def test_credit_institution_identifier(self):
        credit_institution_name = "Test Credit Institution"
        credit_institution_bic = "TESTBIC"
        credit_institution_sat = CreditInstitutionStaticSatellite.objects.create(
            credit_institution_name=credit_institution_name,
            credit_institution_bic=credit_institution_bic,
            hub_entity=self.hub,
        )
        test_hash = hashlib.sha256(
            (credit_institution_name + credit_institution_bic).encode()
        ).hexdigest()
        self.assertEqual(credit_institution_sat.hash_identifier, test_hash)

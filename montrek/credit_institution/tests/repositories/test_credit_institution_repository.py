from django.test import TestCase
from credit_institution.repositories.credit_institution_repository import (
    CreditInstitutionRepository,
)
from credit_institution.tests.factories.credit_institution_factories import (
    CreditInstitutionStaticSatelliteFactory,
)


class TestCreditInstitutionRepository(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.credit_institution_static_satellite = (
            CreditInstitutionStaticSatelliteFactory()
        )

    def test_get_credit_institution_repository_elements(self):
        test_repository = CreditInstitutionRepository(
            self.credit_institution_static_satellite.hub_entity.id
        )
        self.assertEqual(
            test_repository.hub_entity,
            self.credit_institution_static_satellite.hub_entity,
        )
        self.assertEqual(
            test_repository.static_satellite, self.credit_institution_static_satellite
        )

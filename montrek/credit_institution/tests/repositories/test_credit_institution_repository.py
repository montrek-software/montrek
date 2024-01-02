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
        credit_institution_repository = CreditInstitutionRepository(None)
        queries_objects = credit_institution_repository.std_queryset()
        self.assertEqual(queries_objects.count(), 1)
        for field in ('credit_institution_name', 'credit_institution_bic', 'account_upload_method'):
            self.assertEqual(
                getattr(queries_objects.first(),field),
                getattr(self.credit_institution_static_satellite,field),
            )

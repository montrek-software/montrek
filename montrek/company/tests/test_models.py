from django.test import TestCase
from company.tests.factories.company_factories import CompanyStaticSatelliteFactory


class TestCompanyStaticSatellite(TestCase):
    def test_str(self):
        company = CompanyStaticSatelliteFactory.create()
        assert company.__str__() == company.effectual_company_id

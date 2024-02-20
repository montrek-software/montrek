from django.contrib.auth import get_user_model
from django.test import TestCase
from company.tests.factories.company_factories import CompanyStaticSatelliteFactory
from company.repositories.company_repository import CompanyRepository
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class CompanyRepositoryTest(TestCase):
    def setUp(self):
        self.test_countries = CompanyStaticSatelliteFactory.create_batch(3)
        self.user = MontrekUserFactory()

    def test_std_queryset(self):
        test_countries = CompanyRepository().std_queryset()
        self.assertEqual(len(test_countries), 3)
        for i in range(3):
            self.assertEqual(
                test_countries[i].company_name, self.test_countries[i].company_name
            )
            self.assertEqual(
                test_countries[i].bloomberg_ticker, self.test_countries[i].bloomberg_ticker
            )

    def test_create_and_update_data(self):
        input_data = {"company_name": "TestCompany", "bloomberg_ticker": "TST"}
        repository = CompanyRepository(session_data={"user_id": self.user.id})
        repository.std_create_object(input_data)
        test_countries = repository.std_queryset()
        self.assertEqual(len(test_countries), 4)
        self.assertEqual(test_countries[3].company_name, "TestCompany")
        self.assertEqual(test_countries[3].bloomberg_ticker, "TST")
        input_data = {"company_name": "UnitedTestCompany", "bloomberg_ticker": "TST"}
        repository.std_create_object(input_data)
        test_countries = repository.std_queryset()
        self.assertEqual(len(test_countries), 4)
        self.assertEqual(test_countries[3].company_name, "UnitedTestCompany")
        self.assertEqual(test_countries[3].bloomberg_ticker, "TST")

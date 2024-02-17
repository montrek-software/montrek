from django.contrib.auth import get_user_model
from django.test import TestCase
from country.tests.factories.country_factories import CountryStaticSatelliteFactory
from country.repositories.country_repository import CountryRepository
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class CountryRepositoryTest(TestCase):
    def setUp(self):
        self.test_countries = CountryStaticSatelliteFactory.create_batch(3)
        self.user = MontrekUserFactory()

    def test_std_queryset(self):
        test_countries = CountryRepository().std_queryset()
        self.assertEqual(len(test_countries), 3)
        for i in range(3):
            self.assertEqual(
                test_countries[i].country_name, self.test_countries[i].country_name
            )
            self.assertEqual(
                test_countries[i].country_code, self.test_countries[i].country_code
            )

    def test_create_and_update_data(self):
        input_data = {"country_name": "TestCountry", "country_code": "TST"}
        repository = CountryRepository(session_data={"user_id": self.user.id})
        repository.std_create_object(input_data)
        test_countries = repository.std_queryset()
        self.assertEqual(len(test_countries), 4)
        self.assertEqual(test_countries[3].country_name, "TestCountry")
        self.assertEqual(test_countries[3].country_code, "TST")
        input_data = {"country_name": "UnitedTestCountry", "country_code": "TST"}
        repository = CountryRepository(session_data={"user_id": self.user.id})
        repository.std_create_object(input_data)
        test_countries = repository.std_queryset()
        self.assertEqual(len(test_countries), 4)
        self.assertEqual(test_countries[3].country_name, "UnitedTestCountry")
        self.assertEqual(test_countries[3].country_code, "TST")

from django.test import TestCase
from country.tests.factories.country_factories import CountryStaticSatelliteFactory
from country.repositories.country_repository import CountryRepository


class CountryRepositoryTest(TestCase):
    def setUp(self):
        self.test_countries = CountryStaticSatelliteFactory.create_batch(3)

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

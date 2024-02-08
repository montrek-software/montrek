from django.test import TestCase
from country.tests.factories.country_factories import CountryStaticSatelliteFactory

class TestCountryStaticSatellite(TestCase):
    def test_str(self):
        country = CountryStaticSatelliteFactory.create()
        assert country.__str__() == country.country_name

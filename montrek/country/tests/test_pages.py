from django.test import TestCase

from country.pages import CountryPage


class TestCountryPage(TestCase):
    def test_raises_error_if_no_pk(self):
        with self.assertRaises(ValueError) as e:
            CountryPage()
        self.assertEqual(
            str(e.exception), "CountryPage needs pk specified in url!"
        )

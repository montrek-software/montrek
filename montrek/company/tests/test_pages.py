from django.test import TestCase

from company.pages import CompanyPage


class TestCompanyPage(TestCase):
    def test_raises_error_if_no_pk(self):
        with self.assertRaises(ValueError) as e:
            CompanyPage()
        self.assertEqual(
            str(e.exception), "CompanyPage needs pk specified in url!"
        )

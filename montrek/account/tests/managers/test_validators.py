from django.test import TestCase

from django.core.validators import RegexValidator
from account.managers.validators import montrek_iban_validator

class TestValidators(TestCase):

    def test_montrek_iban_validator(self):
        iban_regex = r'^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$'
        validator = RegexValidator(
            regex=iban_regex,
            message="Invalid IBAN format."
        )
        self.assertEqual(validator, montrek_iban_validator())


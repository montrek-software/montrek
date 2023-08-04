from django.core.validators import RegexValidator


def montrek_iban_validator() -> RegexValidator:
    iban_regex = r"^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$"
    return RegexValidator(regex=iban_regex, message="Invalid IBAN format.")

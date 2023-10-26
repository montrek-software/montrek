from django.core.exceptions import ValidationError
import re


def montrek_isin_validator(value):
    """
    Django validator for an ISIN.
    """
    if not re.match(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$', value):
        raise ValidationError("Invalid ISIN format.")

def montrek_wkn_validator(value):
    """
    Django validator for a WKN.
    """
    if not re.match(r'^[A-Z0-9]{6}$', value):
        raise ValidationError("Invalid WKN format.")


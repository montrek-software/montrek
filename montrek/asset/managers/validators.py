from django.core.exceptions import ValidationError
import re

def isin_checksum(isin):
    """
    Calculate the ISIN check digit.
    """
    # Replace letters with numbers using the standard ISIN replacement
    digits = ''
    for char in isin[:-1]:
        if char.isdigit():
            digits += char
        else:
            digits += str(ord(char) - ord('A') + 10)

    # Calculate the checksum
    total = 0
    for num in map(int, str(digits)):
        total = (total * 10 + num) % 97

    return (100 - total) % 10

def montrek_isin_validator(value):
    """
    Django validator for an ISIN.
    """
    if not re.match(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$', value):
        raise ValidationError("Invalid ISIN format.")

    if int(value[-1]) != isin_checksum(value):
        raise ValidationError("Invalid ISIN checksum.")

def montrek_wkn_validator(value):
    """
    Django validator for a WKN.
    """
    if not re.match(r'^[A-Z0-9]{6}$', value):
        raise ValidationError("Invalid WKN format.")


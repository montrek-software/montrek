# Purpose: Utility functions for the model package
from baseclasses.models import MontrekSatelliteABC
from django.db.models.base import ModelBase
from django.core.validators import RegexValidator
from typing import Any, List

def get_hub_ids_by_satellite_attribute(satellite: ModelBase,
                                      field: str,
                                      value: Any) -> List[int]:
    if not isinstance(satellite, ModelBase):
        raise TypeError('satellite must be a BaseModel')
    if not isinstance(field, str):
        raise TypeError('field must be a str')
    satellite_instance = satellite.objects.filter(**{field: value}).all()
    return [instance.hub_entity.id for instance in satellite_instance]

def montrek_iban_validator():
    iban_regex = r'^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$'
    return RegexValidator(
        regex=iban_regex,
        message="Invalid IBAN format."
    )




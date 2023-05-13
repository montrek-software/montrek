# Purpose: Utility functions for the model package
from baseclasses.models import MontrekSatelliteABC
from django.db.models.base import ModelBase
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

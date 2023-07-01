# Purpose: Utility functions for the model package
import copy
from baseclasses.models import MontrekSatelliteABC
from baseclasses.models import MontrekHubABC
from baseclasses.models import MontrekLinkABC
from django.db.models.base import ModelBase
from django.core.validators import RegexValidator
from django.utils import timezone
from typing import Any, List


def new_link_entry(from_hub:MontrekHubABC,
                   to_hub:MontrekHubABC,
                   link_table:MontrekLinkABC) -> None:
    link_table.objects.create(
        from_hub=from_hub,
        to_hub=to_hub)

def new_satellite_entry(hub_entity:MontrekHubABC,
                        satellite_class:MontrekSatelliteABC,
                        **kwargs) -> MontrekSatelliteABC:
    satellite_entity = satellite_class.objects.create(
        hub_entity=hub_entity,
        **kwargs)
    return satellite_entity

def get_hub_ids_by_satellite_attribute(satellite: MontrekSatelliteABC,
                                      field: str,
                                      value: Any) -> List[int]:
    if not isinstance(satellite(), MontrekSatelliteABC):
        raise TypeError('satellite must be a MontrekSatelliteABC')
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

def select_satellite(
                     hub_entity:MontrekHubABC,
                     satellite_class:MontrekSatelliteABC,
                     reference_date:timezone = None,
):
    reference_date = timezone.now() if reference_date is None else reference_date
    satellite_instance = satellite_class.objects.filter(
        hub_entity=hub_entity,
        state_date__lte=reference_date,
    ).order_by('-state_date').first()
    return satellite_instance

def update_satellite(
    satellite_instance:ModelBase,
    **kwargs,
):
    satellite_class = satellite_instance.__class__
    new_satellite_entry = copy.copy(satellite_instance)
    new_satellite_entry.pk = None
    if 'state_date' not in kwargs:
        new_satellite_entry.state_date = timezone.now()
    for key, value in kwargs.items():
        setattr(new_satellite_entry, key, value)
    new_satellite_entry.save()
    return new_satellite_entry

def get_hub_by_id(
    hub_id: int,
    hub_class: MontrekHubABC,
):
    return hub_class.objects.get(id=hub_id)

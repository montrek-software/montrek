# Purpose: Utility functions for the model package
import pandas as pd
import copy
from typing import Any, List, Dict
from baseclasses.models import MontrekSatelliteABC
from baseclasses.models import MontrekHubABC
from baseclasses.models import MontrekLinkABC
from django.db.models.base import ModelBase
from django.utils import timezone


def new_link_entry(from_hub:MontrekHubABC,
                   to_hub:MontrekHubABC,
                   link_table:MontrekLinkABC) -> None:
    existing_link = link_table.objects.filter(
        from_hub=from_hub,
        to_hub=to_hub).first()
    if existing_link:
        #TODO add logging
        return
    link_table.objects.create(
        from_hub=from_hub,
        to_hub=to_hub)

def get_link_to_hub(from_hub:MontrekHubABC,
                    link_table:MontrekLinkABC) -> MontrekHubABC:
    link_instance = link_table.objects.get(
        from_hub=from_hub)
    return link_instance.to_hub

def new_satellite_entry(hub_entity:MontrekHubABC,
                        satellite_class:MontrekSatelliteABC,
                        **kwargs) -> MontrekSatelliteABC:
    satellite_entity = satellite_class.objects.create(
        hub_entity=hub_entity,
        **kwargs
    )
    return satellite_entity

def new_satellites_bunch_from_df(hub_entity:MontrekHubABC,
                                 satellite_class:MontrekSatelliteABC,
                                 import_df:pd.DataFrame,
                                ) -> List[MontrekSatelliteABC]:
    columns = import_df.columns
    satellite_attributes = [{column: row[column] for column in columns} for _, row in import_df.iterrows()]
    return new_satellites_bunch(hub_entity=hub_entity,
                                satellite_class=satellite_class,
                                attributes=satellite_attributes)


def new_satellites_bunch(hub_entity:MontrekHubABC,
                        satellite_class:MontrekSatelliteABC,
                        attributes: List[dict]
                        ) -> MontrekSatelliteABC:
    satellites = [satellite_class(hub_entity=hub_entity, **attribute) for attribute in attributes]
    satellite_entities = satellite_class.objects.bulk_create(satellites)
    return satellite_entities

def get_hub_ids_by_satellite_attribute(satellite: ModelBase,
                                      field: str,
                                      value: Any) -> List[int]:
    if not isinstance(satellite(), MontrekSatelliteABC):
        raise TypeError('satellite must be a MontrekSatelliteABC')
    if not isinstance(field, str):
        raise TypeError('field must be a str')
    satellite_instance = satellite.objects.filter(**{field: value}).all()
    return [instance.hub_entity.id for instance in satellite_instance]

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

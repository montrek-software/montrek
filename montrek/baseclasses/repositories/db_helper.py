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

def new_satellite_entry(satellite_class:MontrekSatelliteABC,
                        hub_entity:MontrekHubABC = None,
                        **kwargs) -> MontrekSatelliteABC:
    if hub_entity is None:
        hub_class = satellite_class._meta.get_field('hub_entity').related_model
        hub_entity = hub_class.objects.create() 
    satellite_entity = satellite_class(
        hub_entity=hub_entity,
        **kwargs
    )
    satellite_update = update_satellite(satellite_entity)
    if satellite_update.id is None:
        satellite_update.save()
    return satellite_update

def new_satellites_bunch_from_df_and_from_hub_link(
    satellite_class:MontrekSatelliteABC,
    import_df:pd.DataFrame,
    from_hub:MontrekHubABC,
    link_table_class:MontrekLinkABC) -> List[MontrekSatelliteABC]:
    satellites = new_satellites_bunch_from_df(
        satellite_class=satellite_class,
        import_df=import_df)
    for satellite in satellites:
        new_link_entry(
            from_hub=from_hub,
            to_hub=satellite.hub_entity,
            link_table=link_table_class)
    return satellites

def new_satellites_bunch_from_df(satellite_class:MontrekSatelliteABC,
                                 import_df:pd.DataFrame,
                                ) -> List[MontrekSatelliteABC]:
    columns = import_df.columns
    satellite_attributes = [{column: row[column] for column in columns} for _, row in import_df.iterrows()]
    return new_satellites_bunch(satellite_class=satellite_class,
                                attributes=satellite_attributes)


def new_satellites_bunch(satellite_class:MontrekSatelliteABC,
                         attributes: List[dict]
                         ) -> List[MontrekSatelliteABC]:
    hub_class = satellite_class._meta.get_field('hub_entity').related_model
    hubs = [hub_class.objects.create() for _ in range(len(attributes))]
    satellites = [satellite_class(hub_entity=hubs[i], **attribute) for i, attribute in enumerate(attributes)]
    satellite_entities = satellite_class.objects.bulk_create(satellites)
    return satellite_entities

def update_satellite(satellite:MontrekSatelliteABC,) -> bool:
    satellite_class = satellite.__class__
    sat_hash_identifier = satellite.get_hash_identifier
    satellite_updates_or_none = (satellite_class.objects
                                .filter(hash_identifier = sat_hash_identifier)
                                .order_by('-state_date')
                                .first()
                               )
    if satellite_updates_or_none is None:
        return satellite
    sat_hash_value = satellite.get_hash_value
    if satellite_updates_or_none.hash_value == sat_hash_value:
        return satellite_updates_or_none
    satellite.hub_entity = satellite_updates_or_none.hub_entity
    satellite.state_date = timezone.now()
    return satellite

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


def get_hub_by_id(
    hub_id: int,
    hub_class: MontrekHubABC,
):
    return hub_class.objects.get(id=hub_id)

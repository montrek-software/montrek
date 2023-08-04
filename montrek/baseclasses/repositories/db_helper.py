# Purpose: Utility functions for the model package
import pandas as pd
import copy
from typing import Any, List, Dict
from baseclasses.models import MontrekSatelliteABC
from baseclasses.models import MontrekHubABC
from baseclasses.models import MontrekLinkABC
from django.db.models.base import ModelBase
from django.db.models import Q
from django.utils import timezone


def new_link_entry(
    from_hub: MontrekHubABC, to_hub: MontrekHubABC, link_table: MontrekLinkABC
) -> None:
    existing_link = link_table.objects.filter(from_hub=from_hub, to_hub=to_hub).first()
    if existing_link:
        # TODO add logging
        return
    link_table.objects.create(from_hub=from_hub, to_hub=to_hub)


def get_link_to_hub(
    from_hub: MontrekHubABC, link_table: MontrekLinkABC
) -> MontrekHubABC:
    # TODO Rename function as we dont return the link, but the to_hub
    link_instance = link_table.objects.get(from_hub=from_hub)
    return link_instance.to_hub


def new_satellite_entry(
    satellite_class: MontrekSatelliteABC, hub_entity: MontrekHubABC = None, **kwargs
) -> MontrekSatelliteABC:
    if hub_entity is None:
        hub_class = satellite_class._meta.get_field("hub_entity").related_model
        hub_entity = hub_class()
    satellite_entity = satellite_class(hub_entity=hub_entity, **kwargs)
    satellite_update = update_satellite(satellite_entity)
    hub_entity = satellite_update.hub_entity
    if hub_entity.id is None:
        hub_entity.save()
    if satellite_update.id is None:
        satellite_update.save()
    return satellite_update


def new_satellites_bunch_from_df_and_from_hub_link(
    satellite_class: MontrekSatelliteABC,
    import_df: pd.DataFrame,
    from_hub: MontrekHubABC,
    link_table_class: MontrekLinkABC,
) -> List[MontrekSatelliteABC]:
    satellites = new_satellites_bunch_from_df(
        satellite_class=satellite_class, import_df=import_df
    )
    for satellite in satellites:
        new_link_entry(
            from_hub=from_hub, to_hub=satellite.hub_entity, link_table=link_table_class
        )
    return satellites


def new_satellites_bunch_from_df(
    satellite_class: MontrekSatelliteABC,
    import_df: pd.DataFrame,
) -> List[MontrekSatelliteABC]:
    columns = import_df.columns
    satellite_attributes = [
        {column: row[column] for column in columns} for _, row in import_df.iterrows()
    ]
    return new_satellites_bunch(
        satellite_class=satellite_class, attributes=satellite_attributes
    )


def new_satellites_bunch(
    satellite_class: MontrekSatelliteABC, attributes: List[dict]
) -> List[MontrekSatelliteABC]:
    hub_class = satellite_class._meta.get_field("hub_entity").related_model
    hubs = [hub_class() for _ in range(len(attributes))]
    satellites = [
        satellite_class(hub_entity=hubs[i], **attribute)
        for i, attribute in enumerate(attributes)
    ]
    satellites_updates = [update_satellite(satellite) for satellite in satellites]
    satellites_updates_new = [
        satellite for satellite in satellites_updates if satellite.id is None
    ]
    # Need to set hash_identifier and hash_value for new satellites manually, since create_bulk does not run the save
    # method but enteres the rows directly in the db
    for satellite in satellites_updates_new:
        satellite.get_hash_identifier
        satellite.get_hash_value
    new_hubs = [
        satellite.hub_entity
        for satellite in satellites_updates_new
        if satellite.hub_entity.id is None
    ]
    hub_class.objects.bulk_create(new_hubs)
    satellite_entities = satellite_class.objects.bulk_create(
        satellites_updates_new,
        batch_size=1000,
    )
    return satellite_entities


def update_satellite(
    satellite: MontrekSatelliteABC,
) -> bool:
    satellite_class = satellite.__class__
    sat_hash_identifier = satellite.get_hash_identifier
    satellite_updates_or_none = (
        satellite_class.objects.filter(hash_identifier=sat_hash_identifier)
        .order_by("-state_date_start")
        .first()
    )
    if satellite_updates_or_none is None:
        return satellite
    sat_hash_value = satellite.get_hash_value
    if satellite_updates_or_none.hash_value == sat_hash_value:
        return satellite_updates_or_none
    satellite.hub_entity = satellite_updates_or_none.hub_entity
    state_date = timezone.now()
    new_state_date = state_date
    satellite_updates_or_none.state_date_end = new_state_date
    satellite_updates_or_none.save()
    satellite.state_date_start = state_date
    return satellite


def update_satellite_from_satellite(
    satellite_instance: MontrekSatelliteABC, **kwargs
) -> MontrekSatelliteABC:
    satellite_class = satellite_instance.__class__
    updated_satellite_entry = copy.copy(satellite_instance)
    updated_satellite_entry.pk = None
    updated_state_date = timezone.now()
    if "state_date_start" in kwargs:
        updated_state_date = kwargs["state_date_start"]
        del kwargs["state_date_start"]
    for key, value in kwargs.items():
        setattr(updated_satellite_entry, key, value)
    updated_satellite_entry.state_date_start = updated_state_date
    satellite_instance.state_date_end = updated_state_date
    satellite_instance.save()
    updated_satellite_entry.save()
    return updated_satellite_entry


def get_hub_ids_by_satellite_attribute(
    satellite: MontrekSatelliteABC, field: str, value: Any
) -> List[int]:
    hubs = get_hubs_by_satellite_attribute(satellite, field, value)
    return [instance.id for instance in hubs]


def get_hubs_by_satellite_attribute(
    satellite: MontrekSatelliteABC, field: str, value: Any
) -> List[MontrekHubABC]:
    if not isinstance(satellite(), MontrekSatelliteABC):
        raise TypeError("satellite must be a MontrekSatelliteABC")
    if not isinstance(field, str):
        raise TypeError("field must be a str")
    satellite_instance = satellite.objects.filter(**{field: value}).all()
    return [instance.hub_entity for instance in satellite_instance]


def select_satellite(
    hub_entity: MontrekHubABC,
    satellite_class: MontrekSatelliteABC,
    reference_date: timezone = None,
):
    # TODO: Rename to better name
    reference_date = timezone.now() if reference_date is None else reference_date
    satellite_instance = satellite_class.objects.filter(
        Q(hub_entity=hub_entity)
        & Q(state_date_start__lte=reference_date)
        & Q(state_date_end__gte=reference_date)
    ).first()
    return satellite_instance


def get_hub_by_id(
    hub_id: int,
    hub_class: MontrekHubABC,
):
    return hub_class.objects.get(id=hub_id)

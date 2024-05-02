import datetime
from typing import Any, Dict, List, Protocol
from dataclasses import dataclass
from django.db.models import QuerySet
from django.utils import timezone
from baseclasses.models import (
    MontrekSatelliteABC,
    MontrekHubABC,
    MontrekTimeSeriesSatelliteABC,
)
from baseclasses.models import LinkTypeEnum


class SatelliteCreationState(Protocol):
    satellite: MontrekSatelliteABC
    state: str


@dataclass
class UpdatedSatelliteCreationState:
    satellite: MontrekSatelliteABC
    updated_sat: MontrekSatelliteABC
    state: str = "updated"


@dataclass
class NewSatelliteCreationState:
    satellite: MontrekSatelliteABC
    state: str = "new"


@dataclass
class ExistingSatelliteCreationState:
    satellite: MontrekSatelliteABC
    state: str = "existing"


class DbCreator:
    def __init__(
        self,
        hub_entity_class: type[MontrekHubABC],
        satellite_classes: list[type[MontrekSatelliteABC]],
    ):
        self.hub_entity = None
        self.satellite_classes = self._sorted_satellite_classes(satellite_classes)

        self.stalled_hubs = {hub_entity_class: []}
        self.stalled_satellites = {
            satellite_class: [] for satellite_class in satellite_classes
        }
        self.stalled_links = {}

    def create(
        self, data: Dict[str, Any], hub_entity: MontrekHubABC, user_id: int
    ) -> None:
        selected_satellites = {"new": [], "existing": [], "updated": []}
        creation_date = timezone.now()
        self.hub_entity = hub_entity
        for satellite_class in self.satellite_classes:
            sat_data = {
                k: v
                for k, v in data.items()
                if k in satellite_class.get_value_field_names()
            }
            if self._is_empty(sat_data):
                continue
            sat_data = self._make_timezone_aware(sat_data)
            sat_data["created_by_id"] = user_id
            sat = satellite_class(hub_entity=self.hub_entity, **sat_data)
            sat = self._process_new_satellite(sat, satellite_class)
            selected_satellites[sat.state].append(sat)
        reference_hub = self._stall_satellites_and_return_reference_hub(
            selected_satellites, creation_date
        )
        self._stall_hub(reference_hub)
        self.stall_links(data, reference_hub, creation_date)
        return reference_hub

    def _make_timezone_aware(self, sat_data: dict) -> dict:
        for key, value in sat_data.items():
            if isinstance(value, datetime.datetime):
                if value.tzinfo is None:
                    sat_data[key] = timezone.make_aware(
                        value, timezone.get_default_timezone()
                    )
        return sat_data

    def save_stalled_objects(self):
        for hub_class, stalled_hubs in self.stalled_hubs.items():
            self._bulk_create_and_update_stalled_objects(stalled_hubs, hub_class)
        for satellite_class, stalled_satellites in self.stalled_satellites.items():
            if "hub_entity_id" in satellite_class.identifier_fields:
                for stalled_satellite in stalled_satellites:
                    stalled_satellite.hub_entity_id = stalled_satellite.hub_entity.id
                    stalled_satellite.get_hash_identifier
                    stalled_satellite.get_hash_value

            self._bulk_create_and_update_stalled_objects(
                stalled_satellites, satellite_class
            )
        for link_class, stalled_links in self.stalled_links.items():
            self._bulk_create_and_update_stalled_objects(stalled_links, link_class)

    def _sorted_satellite_classes(
        self, satellite_classes: list[type[MontrekSatelliteABC]]
    ) -> list[type[MontrekSatelliteABC]]:
        time_series_classes = [
            sat_class
            for sat_class in satellite_classes
            if isinstance(sat_class(), MontrekTimeSeriesSatelliteABC)
        ]
        other_classes = [
            sat_class
            for sat_class in satellite_classes
            if sat_class not in time_series_classes
        ]
        return other_classes + time_series_classes

    def _bulk_create_and_update_stalled_objects(
        self, stalled_objects, stalled_object_class
    ):
        create_objects = [so for so in stalled_objects if so.pk is None]
        stalled_object_class.objects.bulk_create(create_objects)
        update_objects = [so for so in stalled_objects if so.pk is not None]
        stalled_object_class.objects.bulk_update(
            update_objects,
            fields=(
                "state_date_end",
                "state_date_start",
            ),
        )

    def _process_new_satellite(
        self,
        satellite: MontrekSatelliteABC,
        satellite_class: type[MontrekSatelliteABC],
    ) -> SatelliteCreationState:
        # Check if satellite already exists, if it is updated or if it is new
        sat_hash_identifier = satellite.get_hash_identifier
        sat_hash_value = satellite.get_hash_value
        # TODO: Revisit this filter and check if it does not work if more Satellite have the same values
        satellite_updates_or_none = (
            satellite_class.objects.filter(hash_identifier=sat_hash_identifier)
            .order_by("-state_date_start")
            .first()
        )
        if satellite_updates_or_none is None:
            return NewSatelliteCreationState(satellite=satellite)
        self.hub_entity = satellite_updates_or_none.hub_entity
        if satellite_updates_or_none.hash_value == sat_hash_value:
            return ExistingSatelliteCreationState(satellite=satellite_updates_or_none)
        return UpdatedSatelliteCreationState(
            satellite=satellite, updated_sat=satellite_updates_or_none
        )

    def _stall_satellites_and_return_reference_hub(
        self,
        selected_satellites: Dict[str, list[SatelliteCreationState]],
        creation_date: timezone.datetime,
    ):
        reference_hub = self._get_reference_hub(selected_satellites, creation_date)

        self._new_satellites(selected_satellites["new"], reference_hub, creation_date)
        self._update_existing_satellites(
            selected_satellites["existing"], reference_hub, creation_date
        )
        self._update_satellites(
            selected_satellites["updated"], reference_hub, creation_date
        )
        return reference_hub

    def _get_reference_hub(self, selected_satellites, creation_date):
        if selected_satellites["new"]:
            reference_hub = selected_satellites["new"][0].satellite.hub_entity
            self._stall_hub(reference_hub)
            return reference_hub
        elif selected_satellites["existing"]:
            return selected_satellites["existing"][0].satellite.hub_entity
        elif selected_satellites["updated"]:
            return selected_satellites["updated"][0].updated_sat.hub_entity

    def _new_satellites(self, new_satellites, reference_hub, creation_date):
        for satellite_create_state in new_satellites:
            satellite = satellite_create_state.satellite
            satellite.hub_entity = reference_hub
            satellite.state_date_start = creation_date
            # Check if there is already another satellites for this hub and if so, set the state_date_end
            if not reference_hub.pk or satellite.allow_multiple:
                self._stall_satellite(satellite)
                continue
            existing_satellites = satellite.__class__.objects.filter(
                hub_entity=reference_hub,
                state_date_end__gte=creation_date,
            ).order_by("created_at")
            if existing_satellites.count() == 1:
                updated_sat = existing_satellites.first()
                updated_sat.state_date_end = creation_date
                self._stall_satellite(updated_sat)
            self._stall_satellite(satellite)

    def _update_existing_satellites(
        self,
        existing_satellites: List[MontrekSatelliteABC],
        reference_hub: MontrekHubABC,
        creation_date: timezone.datetime,
    ):
        if not existing_satellites:
            return

        old_hub = existing_satellites[0].satellite.hub_entity
        if old_hub == reference_hub:
            return
        self._update_hubs(old_hub, reference_hub, creation_date)

        for satellite_create_state in existing_satellites:
            self._copy_satellite_for_hub(
                satellite_create_state.satellite, reference_hub, creation_date
            )

    def _update_satellites(self, updated_satellites, reference_hub, creation_date):
        for satellite_create_state in updated_satellites:
            self._update_satellite_for_hub(
                satellite_create_state, reference_hub, creation_date
            )

    def _update_hubs(self, old_hub, new_hub, creation_date):
        old_hub.state_date_end = creation_date
        self._stall_hub(old_hub)
        new_hub.state_date_start = creation_date
        self._stall_hub(new_hub)

    def _copy_satellite_for_hub(self, satellite, hub, creation_date):
        satellite.state_date_end = creation_date
        satellite.hub_entity = hub
        satellite.state_date_start = creation_date
        satellite.state_date_end = timezone.make_aware(
            timezone.datetime.max, timezone.get_default_timezone()
        )
        satellite.pk = None
        satellite.id = None
        self._stall_satellite(satellite)

    def _update_satellite_for_hub(
        self, satellite_create_state, reference_hub, created_at
    ):
        old_sat = satellite_create_state.updated_sat
        new_sat = satellite_create_state.satellite
        old_sat.state_date_end = created_at
        self._stall_satellite(old_sat)
        new_sat.hub_entity = reference_hub
        new_sat.state_date_start = created_at
        self._stall_satellite(new_sat)

    def stall_links(self, data, reference_hub, creation_date):
        # Filter all data that are Hubs or lists of Hubs, as they can only be linked to other Hubs
        link_data = self._get_link_data(data)
        for field, values in link_data.items():
            for value in values:
                if value is None:
                    continue
                link_class = getattr(reference_hub.__class__, field).through
                new_link = self.create_new_link(
                    link_class, reference_hub, value, creation_date
                )
                self._stall_link_object(new_link)

    def create_new_link(self, link_class, reference_hub, value, creation_date):
        if link_class.hub_in.field.related_model == reference_hub.__class__:
            new_link = link_class(hub_in=reference_hub, hub_out=value)
            return self._process_link(new_link, "hub_in", creation_date)
        else:
            new_link = link_class(hub_in=value, hub_out=reference_hub)
            return self._process_link(new_link, "hub_out", creation_date)

    def _get_link_data(self, data: dict) -> dict[str, list[MontrekHubABC]]:
        link_data = {}
        for key, value in data.items():
            if isinstance(value, MontrekHubABC):
                link_data[key] = [value]
            elif isinstance(value, (list, QuerySet)):
                many_links = [item for item in value if isinstance(item, MontrekHubABC)]
                if many_links:
                    link_data[key] = many_links
        return link_data

    def _process_link(self, link, hub_field, creation_date):
        if link.link_type in (
            LinkTypeEnum.ONE_TO_ONE,
            LinkTypeEnum.ONE_TO_MANY,
            LinkTypeEnum.MANY_TO_MANY,
        ):
            return self._update_link_if_exists(link, hub_field, creation_date)
        return link

    def _update_link_if_exists(self, link, hub_field, creation_date):
        hub = getattr(link, hub_field)
        if not hub.pk:
            return link
        link_class = link.__class__
        filter_args = {
            f"{hub_field}": getattr(link, hub_field),
            "state_date_end__gt": creation_date,
            "state_date_start__lte": creation_date,
        }
        existing_link = link_class.objects.filter(**filter_args).first()

        if not existing_link:
            return link

        if getattr(existing_link, self._get_opposite_field(hub_field)) == getattr(
            link, self._get_opposite_field(hub_field)
        ):
            return existing_link

        existing_link.state_date_end = creation_date
        existing_link.save()
        link.state_date_start = creation_date
        return link

    def _get_opposite_field(self, field):
        return "hub_out" if field == "hub_in" else "hub_in"

    def _stall_hub(self, stalled_hub):
        if not stalled_hub in self.stalled_hubs[stalled_hub.__class__]:
            self.stalled_hubs[stalled_hub.__class__].append(stalled_hub)

    def _stall_satellite(self, stalled_satellite):
        if (
            not stalled_satellite
            in self.stalled_satellites[stalled_satellite.__class__]
        ):
            self.stalled_satellites[stalled_satellite.__class__].append(
                stalled_satellite
            )

    def _stall_link_object(self, stalled_link):
        if stalled_link.__class__ not in self.stalled_links:
            self.stalled_links[stalled_link.__class__] = [stalled_link]
        else:
            self.stalled_links[stalled_link.__class__].append(stalled_link)

    def _is_empty(self, data: Dict[str, Any]) -> bool:
        data = data.copy()
        data.pop("comment", None)
        return not any(data.values())

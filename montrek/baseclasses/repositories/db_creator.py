import datetime
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Protocol

from baseclasses.errors.montrek_user_error import MontrekError
from baseclasses.models import (
    MontrekHubABC,
    MontrekOneToOneLinkABC,
    MontrekSatelliteABC,
    HubValueDate,
    ValueDateList,
)
from baseclasses.repositories.annotator import Annotator
from django.db import transaction
from django.db.models import JSONField, QuerySet, Q
from django.utils import timezone


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
        annotator: Annotator,
    ):
        self.hub_entity = None
        satellite_classes = annotator.get_satellite_classes()
        self.satellite_classes = self._sorted_satellite_classes(satellite_classes)

        self.stalled_hubs = {annotator.hub_class: []}
        self.stalled_satellites = {
            satellite_class: [] for satellite_class in satellite_classes
        }
        self.stalled_links = {}
        self.stalled_hub_value_dates: dict[type[HubValueDate], list[HubValueDate]] = {}

    def create(
        self, data: Dict[str, Any], hub_entity: MontrekHubABC, user_id: int
    ) -> None:
        selected_satellites = {"new": [], "existing": [], "updated": []}
        creation_date = timezone.now()
        self.hub_entity = hub_entity
        value_date = data.get("value_date", None)
        for satellite_class in self.satellite_classes:
            sat_data = {
                k: v
                for k, v in data.items()
                if k in satellite_class.get_value_field_names()
            }
            if self._is_empty(sat_data):
                continue
            sat_data = self._make_timezone_aware(sat_data)
            sat_data = self._convert_json(sat_data, satellite_class)
            sat_data["created_by_id"] = user_id
            if satellite_class.is_timeseries:
                if value_date is None:
                    raise MontrekError(
                        f"TimeSeriesSatellite needs a value_date: {sat_data}"
                    )
                hub_value_date = self._get_hub_value_date(value_date)
                sat = satellite_class(hub_value_date=hub_value_date, **sat_data)
            else:
                sat = satellite_class(hub_entity=self.hub_entity, **sat_data)
            sat = self._process_new_satellite(sat, satellite_class)
            selected_satellites[sat.state].append(sat)

        self._get_hub_value_date(value_date)
        reference_hub = self._stall_satellites_and_return_reference_hub(
            selected_satellites, creation_date
        )
        self._stall_hub(reference_hub)
        self._stall_links(data, reference_hub, creation_date)
        return reference_hub

    def _make_timezone_aware(self, sat_data: dict) -> dict:
        for key, value in sat_data.items():
            if isinstance(value, datetime.datetime):
                if value.tzinfo is None:
                    sat_data[key] = timezone.make_aware(
                        value, timezone.get_default_timezone()
                    )
        return sat_data

    def _convert_json(self, sat_data: dict, satellite_class: type[MontrekSatelliteABC]):
        for field in satellite_class.get_value_fields():
            if field.name in sat_data and isinstance(field, JSONField):
                value = sat_data[field.name]
                if isinstance(value, str):
                    sat_data[field.name] = json.loads(value.replace("'", '"'))
        return sat_data

    @transaction.atomic
    def save_stalled_objects(self):
        for hub_class, stalled_hubs in self.stalled_hubs.items():
            self._bulk_create_and_update_stalled_objects(stalled_hubs, hub_class)
        for (
            hub_value_date_class,
            stalled_hub_value_dates,
        ) in self.stalled_hub_value_dates.items():
            hub_value_date_class.objects.bulk_create(stalled_hub_value_dates)
        for satellite_class, stalled_satellites in self.stalled_satellites.items():
            if (
                "hub_entity_id" in satellite_class.identifier_fields
                or satellite_class.is_timeseries
            ):
                for stalled_satellite in stalled_satellites:
                    if satellite_class.is_timeseries:
                        stalled_satellite.hub_value_date_id = (
                            stalled_satellite.hub_value_date.id
                        )
                    else:
                        stalled_satellite.hub_entity_id = (
                            stalled_satellite.hub_entity.id
                        )
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
            sat_class for sat_class in satellite_classes if sat_class().is_timeseries
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
        if satellite_class.is_timeseries:
            state_date_end_criterion = Q(
                hub_value_date__hub__state_date_end__gt=timezone.now()
            )
        else:
            state_date_end_criterion = Q(hub_entity__state_date_end__gt=timezone.now())

        satellite_updates_or_none = (
            satellite_class.objects.filter(
                state_date_end_criterion,
                Q(hash_identifier=sat_hash_identifier),
            )
            .order_by("-state_date_start")
            .first()
        )
        if satellite_updates_or_none is None:
            return NewSatelliteCreationState(satellite=satellite)
        if satellite_class.is_timeseries:
            self.hub_entity = satellite_updates_or_none.hub_value_date.hub
        else:
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
        reference_hub = self._get_reference_hub(selected_satellites)

        self._new_satellites(selected_satellites["new"], reference_hub, creation_date)
        self._update_existing_satellites(
            selected_satellites["existing"], reference_hub, creation_date
        )
        self._update_satellites(
            selected_satellites["updated"], reference_hub, creation_date
        )
        return reference_hub

    def _get_reference_hub(self, selected_satellites):
        def _get_hub(satellite):
            if satellite.is_timeseries:
                return satellite.hub_value_date.hub
            return satellite.hub_entity

        if selected_satellites["new"]:
            reference_hub = _get_hub(selected_satellites["new"][0].satellite)
            self._stall_hub(reference_hub)
            return reference_hub
        elif selected_satellites["existing"]:
            return _get_hub(selected_satellites["existing"][0].satellite)
        elif selected_satellites["updated"]:
            return _get_hub(selected_satellites["updated"][0].updated_sat)

        return self.hub_entity

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
        ref_satellite = existing_satellites[0].satellite
        if ref_satellite.is_timeseries:
            old_hub = ref_satellite.hub_value_date.hub
        else:
            old_hub = ref_satellite.hub_entity
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
        self.hub_entity = new_hub

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

    def _stall_links(self, data, reference_hub, creation_date):
        # Filter all data that are Hubs or lists of Hubs, as they can only be linked to other Hubs
        link_data = self._get_link_data(data)
        for field, values in link_data.items():
            link_class = getattr(reference_hub.__class__, field).through
            values = [v for v in values if v]
            new_links = self._create_new_links(
                link_class, reference_hub, values, creation_date
            )
            for new_link in new_links:
                self._stall_link_object(new_link)

    def _create_new_links(self, link_class, reference_hub, values, creation_date):
        if link_class.hub_in.field.related_model == reference_hub.__class__:
            new_links = [
                link_class(hub_in=reference_hub, hub_out=value) for value in values
            ]
            return self._update_links_if_exist(new_links, "hub_in", creation_date)
        else:
            new_links = [
                link_class(hub_in=value, hub_out=reference_hub) for value in values
            ]
            return self._update_links_if_exist(new_links, "hub_out", creation_date)

    def _get_link_data(self, data: dict) -> dict[str, list[MontrekHubABC]]:
        link_data = {}
        for key, value in data.items():
            if isinstance(value, HubValueDate):
                link_data[key] = [value.hub]
            elif isinstance(value, MontrekHubABC):
                link_data[key] = [value]
            elif isinstance(value, (list, QuerySet)):
                many_links = [
                    item.hub for item in value if isinstance(item, HubValueDate)
                ]
                many_links += [
                    item for item in value if isinstance(item, MontrekHubABC)
                ]
                if many_links:
                    link_data[key] = many_links
        return link_data

    def _update_links_if_exist(self, links, hub_field, creation_date):
        hub = getattr(links[0], hub_field)
        if not hub.pk:
            return links
        link_class = links[0].__class__
        is_one_to_one_link = isinstance(links[0], MontrekOneToOneLinkABC)
        if is_one_to_one_link and len(links) > 1:
            raise MontrekError(
                f"Try to link mulitple items to OneToOne Link {link_class}"
            )
        filter_args = {
            f"{hub_field}": hub,
            "state_date_end__gt": creation_date,
            "state_date_start__lte": creation_date,
        }
        existing_links = link_class.objects.filter(**filter_args).all()
        if not existing_links:
            return links
        opposite_field = self._get_opposite_field(hub_field)
        opposite_hubs = [getattr(link, opposite_field) for link in links]
        filter_kwargs = {f"{opposite_field}__in": opposite_hubs}
        continued_links = existing_links.filter(**filter_kwargs).all()
        if is_one_to_one_link:
            discontinued_links = existing_links.exclude(**filter_kwargs).all()
            for link in discontinued_links:
                link.state_date_end = creation_date
                link.save()
        continued_opposite_hubs = [
            getattr(link, opposite_field) for link in continued_links
        ]
        new_links = [
            link
            for link in links
            if getattr(link, opposite_field) not in continued_opposite_hubs
        ]
        for link in new_links:
            link.state_date_start = creation_date
        return new_links + list(continued_links)

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

    def _stall_hub_value_date_object(self, stalled_hub_value_date: HubValueDate):
        if stalled_hub_value_date.__class__ not in self.stalled_hub_value_dates:
            self.stalled_hub_value_dates[stalled_hub_value_date.__class__] = [
                stalled_hub_value_date
            ]
        else:
            self.stalled_hub_value_dates[stalled_hub_value_date.__class__].append(
                stalled_hub_value_date
            )

    def _hub_value_date_stalled(
        self,
        hub_entity: MontrekHubABC | None,
        value_date: timezone.datetime | str | None,
    ) -> HubValueDate | None:
        d1 = timezone.datetime.now()
        hub_value_date_class = hub_entity.hub_value_date.field.model
        stalled_hub_value_dates = self.stalled_hub_value_dates.get(
            hub_value_date_class, []
        )
        if isinstance(value_date, str):
            value_date = timezone.datetime.fromisoformat(value_date).date()
        for hub_value_date in stalled_hub_value_dates:
            comp_value_date = hub_value_date.value_date_list.value_date
            if isinstance(comp_value_date, str):
                comp_value_date = timezone.datetime.fromisoformat(
                    comp_value_date
                ).date()
            if hub_value_date.hub == hub_entity and comp_value_date == value_date:
                return hub_value_date
        d2 = timezone.datetime.now()
        print(f"Time to check hub_value_date_stalled: {d2-d1}")
        return None

    def _get_hub_value_date(self, value_date: timezone.datetime | None) -> HubValueDate:
        hub_entity = self.hub_entity
        hub_value_date_class = hub_entity.hub_value_date.field.model
        # hub_value_date_stalled = self._hub_value_date_stalled(hub_entity, value_date)
        # if hub_value_date_stalled:
        #     return hub_value_date_stalled
        existing_value_date_list = ValueDateList.objects.filter(value_date=value_date)
        if existing_value_date_list.count() == 0:
            value_date_list = ValueDateList(value_date=value_date)
            value_date_list.save()
        elif existing_value_date_list.count() == 1:
            value_date_list = existing_value_date_list.first()
        else:
            raise MontrekError(
                f"Severe Error: Multiple ValueDateList objects for date {value_date}"
            )
        if hub_entity.id is None:
            hub_value_date = hub_value_date_class(
                hub=hub_entity, value_date_list=value_date_list
            )
            self._stall_hub_value_date_object(hub_value_date)
            return hub_value_date
        existing_hub_value_date = hub_value_date_class.objects.filter(
            hub=hub_entity,
            value_date_list=value_date_list,
        )
        if existing_hub_value_date.count() == 1:
            return existing_hub_value_date.first()
        if existing_hub_value_date.count() > 1:
            raise MontrekError(
                f"Severe Error: Multiple HubValueDate objects for hub {hub_entity} and date None"
            )
        hub_value_date = hub_value_date_class(
            hub=hub_entity, value_date_list=value_date_list
        )
        self._stall_hub_value_date_object(hub_value_date)
        return hub_value_date

    def _is_empty(self, data: Dict[str, Any]) -> bool:
        data = data.copy()
        data.pop("comment", None)
        return not any(data.values())

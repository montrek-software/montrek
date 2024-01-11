from typing import List, Type, Dict, Any
from dataclasses import dataclass
from django.db.models import QuerySet
from django.utils import timezone
from baseclasses.models import MontrekSatelliteABC, MontrekHubABC, MontrekLinkABC
from baseclasses.models import LinkTypeEnum


@dataclass
class SatelliteCreationState:
    satellite: MontrekSatelliteABC


@dataclass
class UpdatedSatelliteCreationState(SatelliteCreationState):
    updated_sat: MontrekSatelliteABC
    state: str = "updated"


@dataclass
class NewSatelliteCreationState(SatelliteCreationState):
    state: str = "new"


@dataclass
class ExistingSatelliteCreationState(SatelliteCreationState):
    state: str = "existing"


class DbCreator:
    def __init__(
        self,
        hub_entity: MontrekHubABC,
        satellite_classes: List[Type[MontrekSatelliteABC]],
    ):
        # TODO: remove hub_entity
        self.hub_entity = hub_entity
        self.satellite_classes = satellite_classes

    def create(self, data: Dict[str, Any]) -> None:
        selected_satellites = {"new": [], "existing": [], "updated": []}
        creation_date = timezone.datetime.now()
        self.hub_entity.save()
        for satellite_class in self.satellite_classes:
            sat_data = {
                k: v
                for k, v in data.items()
                if k in satellite_class.get_value_field_names()
            }
            if len(sat_data) == 0:
                continue
            sat = satellite_class(hub_entity=self.hub_entity, **sat_data)
            sat = self._process_new_satellite(sat, satellite_class)
            selected_satellites[sat.state].append(sat)
        reference_hub = self._save_satellites_and_return_reference_hub(
            selected_satellites, creation_date
        )
        self.create_links(data, reference_hub, creation_date)
        return reference_hub

    def _process_new_satellite(
        self,
        satellite: MontrekSatelliteABC,
        satellite_class: Type[MontrekSatelliteABC],
    ) -> SatelliteCreationState:
        # Check if satellite already exists, if it is updating or if it is new
        sat_hash_identifier = satellite.get_hash_identifier
        # TODO: Revisit thsi filter and if it does not work if more Satellite have the same values
        satellite_updates_or_none = (
            satellite_class.objects.filter(hash_identifier=sat_hash_identifier)
            .order_by("-state_date_start")
            .first()
        )
        if satellite_updates_or_none is None:
            return NewSatelliteCreationState(satellite=satellite)
        sat_hash_value = satellite.get_hash_value
        if satellite_updates_or_none.get_hash_value == sat_hash_value:
            return ExistingSatelliteCreationState(satellite=satellite_updates_or_none)
        return UpdatedSatelliteCreationState(
            satellite=satellite, updated_sat=satellite_updates_or_none
        )

    def _save_satellites_and_return_reference_hub(
        self,
        selected_satellites: Dict[str, List[SatelliteCreationState]],
        creation_date: timezone.datetime,
    ):
        reference_hub = self._get_reference_hub(selected_satellites, creation_date)
        self._remove_not_used_hub(reference_hub)

        self._save_new_satellites(
            selected_satellites["new"], reference_hub, creation_date
        )
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
            reference_hub.save()
            return reference_hub
        elif selected_satellites["existing"]:
            return selected_satellites["existing"][0].satellite.hub_entity
        elif selected_satellites["updated"]:
            return selected_satellites["updated"][0].updated_sat.hub_entity

    def _remove_not_used_hub(self, reference_hub):
        if self.hub_entity != reference_hub:
            self.hub_entity.delete()

    def _save_new_satellites(self, new_satellites, reference_hub, creation_date):
        for satellite_create_state in new_satellites:
            satellite = satellite_create_state.satellite
            satellite.hub_entity = reference_hub
            # Check if there is already another satellites for this hub and if so, set the state_date_end
            existing_satellites = satellite.__class__.objects.filter(
                hub_entity=reference_hub,
                state_date_end__gte=creation_date,
            ).order_by("created_at")
            if existing_satellites.count() == 1:
                updated_sat = existing_satellites.first()
                updated_sat.state_date_end = creation_date
                updated_sat.save()
                satellite.state_date_start = creation_date
            satellite.save()

    def _update_existing_satellites(
        self, existing_satellites, reference_hub, creation_date
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
        old_hub.save()
        new_hub.state_date_start = creation_date
        new_hub.save()

    def _copy_satellite_for_hub(self, satellite, hub, creation_date):
        satellite.state_date_end = creation_date
        satellite.save()
        satellite.hub_entity = hub
        satellite.state_date_start = creation_date
        satellite.state_date_end = timezone.datetime.max
        satellite.pk = None
        satellite.id = None
        satellite.save()

    def _update_satellite_for_hub(
        self, satellite_create_state, reference_hub, created_at
    ):
        old_sat = satellite_create_state.updated_sat
        new_sat = satellite_create_state.satellite
        old_sat.state_date_end = created_at
        old_sat.save()
        new_sat.hub_entity = reference_hub
        new_sat.state_date_start = created_at
        new_sat.save()

    def create_links(self, data, reference_hub, creation_date):
        for field, value in data.items():
            if value is None or not hasattr(reference_hub, field):
                continue

            link_class = getattr(reference_hub, field).through
            new_link = self.create_new_link(
                link_class, reference_hub, value, creation_date
            )
            new_link.save()

    def create_new_link(self, link_class, reference_hub, value, creation_date):
        if link_class.hub_in.field.related_model == reference_hub.__class__:
            new_link = link_class(hub_in=reference_hub, hub_out=value)
            return self._process_link(new_link, "hub_in", creation_date)
        else:
            new_link = link_class(hub_in=value, hub_out=reference_hub)
            return self._process_link(new_link, "hub_out", creation_date)

    def _process_link(self, link, hub_field, creation_date):
        if link.link_type in (LinkTypeEnum.ONE_TO_ONE, LinkTypeEnum.ONE_TO_MANY):
            return self._update_link_if_exists(link, hub_field, creation_date)
        return link

    def _update_link_if_exists(self, link, hub_field, creation_date):
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

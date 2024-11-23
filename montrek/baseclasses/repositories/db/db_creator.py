import datetime
from typing import Any

from baseclasses.errors.montrek_user_error import MontrekError
from baseclasses.models import (
    HubValueDate,
    MontrekHubABC,
    MontrekSatelliteABC,
    ValueDateList,
)
from baseclasses.repositories.db.db_staller import DbStaller
from django.db.models import Q
from django.utils import timezone

DataDict = dict[str, Any]


class DbCreator:
    def __init__(self, db_staller: DbStaller, user_id: int):
        self.db_staller = db_staller
        self.user_id = user_id
        self.hub: MontrekHubABC | None = None
        self.hub_value_date: HubValueDate | None = None
        self.value_date_list: ValueDateList | None = None

    def create(self, data: DataDict):
        data = self._enrich_data(data)
        self._create_static_satellites(data)
        self._stall_hub()
        self._set_static_satellites_hub()
        self._set_value_date_list(data)
        self._stall_hub_value_date()

    def _enrich_data(self, data: DataDict) -> DataDict:
        data["created_by_id"] = self.user_id
        data = self._make_timezone_aware(data)
        return data

    def _create_static_satellites(self, data: DataDict):
        for sat_class in self.db_staller.get_static_satellite_classes():
            sat_data = self._get_satellite_data(data, sat_class)
            if self._is_sat_data_empty(sat_data):
                continue
            sat = sat_class(**sat_data)
            self._process_static_satellite(sat)

    def _make_timezone_aware(self, sat_data: DataDict) -> DataDict:
        for key, value in sat_data.items():
            if isinstance(value, datetime.datetime):
                if value.tzinfo is None:
                    sat_data[key] = timezone.make_aware(
                        value, timezone.get_default_timezone()
                    )
        return sat_data

    def _get_satellite_data(
        self, data: DataDict, sat_class: type[MontrekSatelliteABC]
    ) -> DataDict:
        return {
            key: value
            for key, value in data.items()
            if key in sat_class.get_value_field_names() + ["created_by_id"]
        }

    def _process_static_satellite(self, sat: MontrekSatelliteABC):
        state_date_end_criterion = Q(hub_entity__state_date_end__gt=timezone.now())
        existing_sat = self._get_existing_satellite(sat, state_date_end_criterion)
        if existing_sat is None:
            self.db_staller.stall_new_satellite(sat)
            return
        self.hub = existing_sat.hub_entity

        # if satellite_class.is_timeseries:
        #     self.hub_entity = satellite_updates_or_none.hub_value_date.hub
        # else:
        #     self.hub_entity = satellite_updates_or_none.hub_entity
        # if satellite_updates_or_none.hash_value == sat_hash_value:
        #     return ExistingSatelliteCreationState(satellite=satellite_updates_or_none)
        # return UpdatedSatelliteCreationState(
        #     satellite=satellite, updated_sat=satellite_updates_or_none
        # )
        #

    def _set_value_date_list(self, data: DataDict):
        value_date = data.get("value_date", None)
        existing_value_date_list = ValueDateList.objects.filter(value_date=value_date)
        if existing_value_date_list.count() == 0:
            value_date_list = ValueDateList(value_date=value_date)
            value_date_list.save()
            self.value_date_list = value_date_list
        elif existing_value_date_list.count() == 1:
            self.value_date_list = existing_value_date_list.first()
        else:
            raise MontrekError(
                f"Severe Error: Multiple ValueDateList objects for date {value_date}"
            )

    def _stall_hub(self):
        if not self.hub:
            self.hub = self.db_staller.hub_class(created_by_id=self.user_id)
            self.db_staller.stall_hub(self.hub)

    def _stall_hub_value_date(self):
        if self.hub.id is None:
            hub_value_date = self.db_staller.hub_value_date_class(
                hub=self.hub, value_date_list=self.value_date_list
            )
            self.db_staller.stall_hub_value_date(hub_value_date)
            return

    def _set_static_satellites_hub(self):
        for sat_class in self.db_staller.get_static_satellite_classes():
            sats = self.db_staller.get_new_satellites()[sat_class]
            for sat in sats:
                sat.hub_entity = self.hub

    def _get_existing_satellite(
        self, sat: MontrekSatelliteABC, state_date_end_criterion: Q
    ) -> MontrekSatelliteABC | None:
        # Check if satellite already exists, if it is updated or if it is new
        sat_hash_identifier = sat.get_hash_identifier
        satellite_class = type(sat)

        return (
            satellite_class.objects.filter(
                state_date_end_criterion,
                Q(hash_identifier=sat_hash_identifier),
            )
            .order_by("-state_date_start")
            .first()
        )

    def _is_sat_data_empty(self, data: DataDict) -> bool:
        data = data.copy()
        data.pop("comment", None)
        data.pop("created_by_id", None)
        return not any(data.values())

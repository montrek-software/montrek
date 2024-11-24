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
SatelliteDict = dict[type[MontrekSatelliteABC], MontrekSatelliteABC]


class DbCreator:
    def __init__(self, db_staller: DbStaller, user_id: int):
        self.db_staller = db_staller
        self.data: DataDict = {}
        self.user_id = user_id
        self.hub: MontrekHubABC | None = None
        self.hub_value_date: HubValueDate | None = None
        self.value_date_list: ValueDateList | None = None
        self.creation_date = db_staller.creation_date
        self.new_satellites: SatelliteDict = {}
        self.existing_satellites: SatelliteDict = {}
        self.updated_satellites: SatelliteDict = {}

    def create(self, data: DataDict):
        self.data = data
        self._enrich_data()
        self._create_static_satellites()
        self._stall_hub()
        self._set_static_satellites_hub()
        self._set_value_date_list()
        self._stall_hub_value_date()
        self._create_ts_satellites()

    def _enrich_data(self):
        self.data["created_by_id"] = self.user_id
        self._make_timezone_aware()

    def _create_static_satellites(self):
        for sat_class in self.db_staller.get_static_satellite_classes():
            sat_data = self._get_satellite_data(sat_class)
            if self._is_sat_data_empty(sat_data):
                continue
            sat = sat_class(**sat_data, state_date_start=self.creation_date)
            self._process_static_satellite(sat)

    def _create_ts_satellites(self):
        for sat_class in self.db_staller.get_ts_satellite_classes():
            sat_data = self._get_satellite_data(sat_class)
            if self._is_sat_data_empty(sat_data):
                continue
            sat = sat_class(
                **sat_data,
                state_date_start=self.creation_date,
                hub_value_date=self.hub_value_date,
            )
            self._process_ts_satellite(sat)

    def _make_timezone_aware(self):
        for key, value in self.data.items():
            if isinstance(value, datetime.datetime):
                if value.tzinfo is None:
                    self.data[key] = timezone.make_aware(
                        value, timezone.get_default_timezone()
                    )

    def _get_satellite_data(self, sat_class: type[MontrekSatelliteABC]):
        return {
            key: value
            for key, value in self.data.items()
            if key in sat_class.get_value_field_names() + ["created_by_id"]
        }

    def _process_static_satellite(self, sat: MontrekSatelliteABC):
        state_date_end_criterion = Q(hub_entity__state_date_end__gt=timezone.now())
        existing_sat = self._get_existing_satellite(sat, state_date_end_criterion)
        if existing_sat is None:
            self._stall_new_satellite(sat)
            self._close_existing_sat_if_hub_is_forced(sat)
            return
        self.hub = existing_sat.hub_entity
        self._updated_satellite(sat, existing_sat)

    def _process_ts_satellite(self, sat: MontrekSatelliteABC):
        state_date_end_criterion = Q(
            hub_value_date__hub__state_date_end__gt=timezone.now()
        )
        existing_sat = self._get_existing_satellite(sat, state_date_end_criterion)
        if existing_sat is None:
            self._stall_new_satellite(sat)
            return
        self.hub_value_date = existing_sat.hub_value_date
        self._updated_satellite(sat, existing_sat)

    def _stall_new_satellite(self, sat: MontrekSatelliteABC):
        self.db_staller.stall_new_satellite(sat)
        sat_class = type(sat)
        self.new_satellites[sat_class] = sat

    def _stall_updated_satellite(self, sat: MontrekSatelliteABC):
        self.db_staller.stall_updated_satellite(sat)
        sat_class = type(sat)
        self.updated_satellites[sat_class] = sat

    def _set_value_date_list(self):
        value_date = self.data.get("value_date", None)
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
        if "hub_entity_id" in self.data:
            self.hub = self.db_staller.hub_class.objects.get(
                id=self.data["hub_entity_id"]
            )
        if self.hub:
            return
        self.hub = self.db_staller.hub_class(
            created_by_id=self.user_id, state_date_start=self.creation_date
        )
        self.db_staller.stall_hub(self.hub)

    def _stall_hub_value_date(self):
        if self.hub.id is not None:
            self.hub_value_date = self.db_staller.hub_value_date_class.objects.get(
                hub=self.hub, value_date_list=self.value_date_list
            )
            return
        self.hub_value_date = self.db_staller.hub_value_date_class(
            hub=self.hub, value_date_list=self.value_date_list
        )
        self.db_staller.stall_hub_value_date(self.hub_value_date)

    def _set_static_satellites_hub(self):
        self._reset_hub_if_new_and_existing()
        for sat_class, sat in self.new_satellites.items():
            if sat_class.is_timeseries:
                continue
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

    def _updated_satellite(
        self, sat: MontrekSatelliteABC, existing_sat: MontrekSatelliteABC
    ):
        if existing_sat.get_hash_value == sat.get_hash_value:
            self.existing_satellites[existing_sat.__class__] = existing_sat
            return
        existing_sat.state_date_end = self.creation_date
        sat.state_date_start = self.creation_date
        self._stall_new_satellite(sat)
        self._stall_updated_satellite(existing_sat)

    def _reset_hub_if_new_and_existing(self):
        # if there are new and existing satellites stalled, treat every existing satellite as new
        if len(self.existing_satellites) == 0:
            return
        if len(self.new_satellites) == 0:
            return
        if any(
            [sat_class in self.updated_satellites for sat_class in self.new_satellites]
        ):
            return
        if "hub_entity_id" in self.data:
            return
        self.hub = None
        for existing_sat in self.existing_satellites.values():
            self._close_and_renew_satellite(existing_sat)
        self._stall_hub()

    def _close_and_renew_satellite(self, existing_sat: MontrekSatelliteABC):
        old_hub = existing_sat.hub_entity
        old_hub.state_date_end = self.db_staller.creation_date
        self.db_staller.stall_updated_hub(old_hub)
        existing_sat.state_date_end = self.db_staller.creation_date
        self.db_staller.stall_updated_satellite(existing_sat)
        existing_sat.state_date_end = self.creation_date
        existing_sat.hub_entity = None
        existing_sat.state_date_start = self.creation_date
        existing_sat.state_date_end = timezone.make_aware(
            timezone.datetime.max, timezone.get_default_timezone()
        )
        existing_sat.pk = None
        existing_sat.id = None
        self._stall_new_satellite(existing_sat)

    def _close_existing_sat_if_hub_is_forced(self, sat: MontrekSatelliteABC):
        if "hub_entity_id" not in self.data:
            return
        latest_sat = sat.__class__.objects.filter(
            hub_entity_id=self.data["hub_entity_id"]
        ).latest("state_date_start")
        latest_sat.state_date_end = self.creation_date
        self.db_staller.stall_updated_satellite(latest_sat)

    def _is_sat_data_empty(self, data: DataDict) -> bool:
        data = data.copy()
        data.pop("comment", None)
        data.pop("created_by_id", None)
        data.pop("value_date", None)
        return not any(data.values())

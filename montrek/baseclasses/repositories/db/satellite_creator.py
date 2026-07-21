import datetime

from baseclasses.models import MontrekHubABC, MontrekSatelliteABC
from baseclasses.repositories.db.typing import DataDict
from baseclasses.typing import HubValueDateProtocol


class SatelliteCreator:
    def create_static_satellite(
        self,
        sat_class: type[MontrekSatelliteABC],
        data: DataDict,
        creation_date: datetime.date,
        hub: MontrekHubABC | None = None,
        existing_sat: MontrekSatelliteABC | None = None,
        strict_none_semantics: bool = False,
    ) -> MontrekSatelliteABC | None:
        sat_data = self.get_satellite_data(sat_class, data)
        if self.is_sat_data_empty(sat_data, strict_none_semantics):
            return None
        if existing_sat is not None:
            sat_data = self._fill_missing_fields_from_existing(
                sat_class, sat_data, data, existing_sat
            )
        sat_data["state_date_start"] = creation_date
        if hub is not None:
            sat_data["hub_entity"] = hub
        return sat_class(**sat_data)

    def create_ts_satellite(
        self,
        sat_class: type[MontrekSatelliteABC],
        data: DataDict,
        creation_date: datetime.date,
        hub_value_date: HubValueDateProtocol | None = None,
        existing_sat: MontrekSatelliteABC | None = None,
        strict_none_semantics: bool = False,
    ) -> MontrekSatelliteABC | None:
        sat_data = self.get_satellite_data(sat_class, data)
        if self.is_sat_data_empty(sat_data, strict_none_semantics):
            return None
        if existing_sat is not None:
            sat_data = self._fill_missing_fields_from_existing(
                sat_class, sat_data, data, existing_sat
            )
        sat_data["state_date_start"] = creation_date
        if hub_value_date is not None:
            sat_data["hub_value_date"] = hub_value_date
        return sat_class(
            **sat_data,
        )

    def _fill_missing_fields_from_existing(
        self,
        sat_class: type[MontrekSatelliteABC],
        sat_data: DataDict,
        data: DataDict,
        existing_sat: MontrekSatelliteABC,
    ) -> DataDict:
        """
        Carry over values from the previous satellite version for any value field
        that was not explicitly supplied in ``data``, so partial updates don't reset
        untouched fields back to their model defaults. A field explicitly set to
        None in ``data`` is still respected.
        """
        for field_name in sat_class.get_value_field_names():
            if field_name in data:
                continue
            sat_data[field_name] = getattr(existing_sat, field_name)
        return sat_data

    def get_satellite_data(self, sat_class: type[MontrekSatelliteABC], data: DataDict):
        return {
            key: value
            for key, value in data.items()
            if key in sat_class.get_value_field_names() + ["created_by_id"]
        }

    def is_sat_data_empty(
        self, data: DataDict, strict_none_semantics: bool = False
    ) -> bool:
        data = data.copy()
        data.pop("comment", None)
        data.pop("created_by_id", None)
        data.pop("value_date", None)
        if strict_none_semantics:
            # Caller (e.g. a single explicit create_by_dict update) only ever
            # includes keys it actually means to set, so an explicit None is a
            # real "clear this field" instruction and must not be treated as
            # "nothing to do here". Batch/DataFrame rows can't make that
            # distinction (a NaN cell may just mean "not applicable to this
            # row"), so they keep the value-based emptiness check below.
            return len(data) == 0
        return all(dt is None for dt in data.values())

import datetime
from typing import Optional

from baseclasses.models import MontrekHubABC, MontrekSatelliteABC
from baseclasses.repositories.db.typing import DataDict
from baseclasses.typing import HubValueDateProtocol


class SatelliteCreator:
    def create_static_satellite(
        self,
        sat_class: type[MontrekSatelliteABC],
        data: DataDict,
        creation_date: datetime.date,
        hub: MontrekHubABC,
    ) -> Optional[MontrekSatelliteABC]:
        sat_data = self.get_satellite_data(sat_class, data)
        if self.is_sat_data_empty(sat_data):
            return None
        return sat_class(**sat_data, state_date_start=creation_date, hub_entity=hub)

    def create_ts_satellite(
        self,
        sat_class: type[MontrekSatelliteABC],
        data: DataDict,
        creation_date: datetime.date,
        hub_value_date: HubValueDateProtocol,
    ) -> Optional[MontrekSatelliteABC]:
        sat_data = self.get_satellite_data(sat_class, data)
        if self.is_sat_data_empty(sat_data):
            return None
        return sat_class(
            **sat_data,
            state_date_start=creation_date,
            hub_value_date=hub_value_date,
        )

    def get_satellite_data(self, sat_class: type[MontrekSatelliteABC], data: DataDict):
        return {
            key: value
            for key, value in data.items()
            if key in sat_class.get_value_field_names() + ["created_by_id"]
        }

    def is_sat_data_empty(self, data: DataDict) -> bool:
        data = data.copy()
        data.pop("comment", None)
        data.pop("created_by_id", None)
        data.pop("value_date", None)
        return all(dt is None for dt in data.values())

from typing import Protocol

from baseclasses.models import (
    HubValueDate,
    MontrekHubABC,
    MontrekLinkABC,
    MontrekSatelliteABC,
)
from baseclasses.repositories.annotator import Annotator
from baseclasses.typing import HubValueDateProtocol, MontrekHubProtocol
from django.utils import timezone

StalledSatelliteDict = dict[type[MontrekSatelliteABC], list[MontrekSatelliteABC]]

StalledHubDict = dict[type[MontrekHubABC], list[MontrekHubABC]]
StalledHubValueDateDict = dict[type[HubValueDate], list[HubValueDate]]
StalledLinksDict = dict[type[MontrekLinkABC], list[MontrekLinkABC]]


StalledObject = MontrekSatelliteABC | MontrekHubABC | HubValueDate | MontrekLinkABC

StalledDicts = (
    StalledSatelliteDict | StalledHubDict | StalledHubValueDateDict | StalledLinksDict
)


class DbStallerProtocol(Protocol):
    hub_class: type[MontrekHubProtocol]
    hub_value_date_class: type[HubValueDateProtocol]

    def get_static_satellite_classes(self) -> list[type[MontrekSatelliteABC]]: ...
    def get_ts_satellite_classes(self) -> list[type[MontrekSatelliteABC]]: ...


class DbStaller:
    def __init__(self, annotator: Annotator):
        self.annotator = annotator
        self.new_satellites: StalledSatelliteDict = {
            sat_class: [] for sat_class in annotator.annotated_satellite_classes
        }
        self.updated_satellites: StalledSatelliteDict = {
            sat_class: [] for sat_class in annotator.annotated_satellite_classes
        }
        self.hub_class: type[MontrekHubProtocol] = annotator.hub_class
        self.hubs: StalledHubDict = {self.hub_class: []}
        self.updated_hubs: StalledHubDict = {self.hub_class: []}
        self.hub_value_date_class = self.hub_class.hub_value_date.field.model
        self.hub_value_dates: StalledHubValueDateDict = {self.hub_value_date_class: []}
        self.links: StalledLinksDict = {
            link_class: [] for link_class in annotator.annotated_link_classes
        }
        self.updated_links: StalledLinksDict = {
            link_class: [] for link_class in annotator.annotated_link_classes
        }
        self.creation_date = timezone.now()

    def stall_hub(self, new_hub: MontrekHubABC):
        self._add_stalled_object(new_hub, self.hubs)

    def stall_updated_hub(self, new_hub: MontrekHubABC):
        self._add_stalled_object(new_hub, self.updated_hubs)

    def stall_hub_value_date(self, new_hub_value_date: HubValueDate):
        self._add_stalled_object(new_hub_value_date, self.hub_value_dates)

    def stall_new_satellite(self, new_satellite: MontrekSatelliteABC):
        self._add_stalled_object(new_satellite, self.new_satellites)

    def stall_updated_satellite(self, updated_satellite: MontrekSatelliteABC):
        self._add_stalled_object(updated_satellite, self.updated_satellites)

    def stall_links(self, links: list[MontrekLinkABC]):
        for link in links:
            self._add_stalled_object(link, self.links)

    def stall_updated_links(self, links: list[MontrekLinkABC]):
        for link in links:
            self._add_stalled_object(link, self.updated_links)

    def get_hubs(self) -> StalledHubDict:
        return self.hubs

    def get_updated_hubs(self) -> StalledHubDict:
        return self.updated_hubs

    def get_hub_value_dates(self) -> StalledHubValueDateDict:
        return self.hub_value_dates

    def get_new_satellites(self) -> StalledSatelliteDict:
        return self.new_satellites

    def get_updated_satellites(self) -> StalledSatelliteDict:
        return self.updated_satellites

    def get_links(self) -> StalledLinksDict:
        return self.links

    def get_updated_links(self) -> StalledLinksDict:
        return self.updated_links

    def get_static_satellite_classes(self) -> list[type[MontrekSatelliteABC]]:
        return [
            sat_class
            for sat_class in self.new_satellites.keys()
            if not sat_class.is_timeseries
        ]

    def get_ts_satellite_classes(self) -> list[type[MontrekSatelliteABC]]:
        return [
            sat_class
            for sat_class in self.new_satellites.keys()
            if sat_class.is_timeseries
        ]

    def clean_hubs(self):
        self.hubs: StalledHubDict = {self.hub_class: []}
        self.updated_hubs: StalledHubDict = {self.hub_class: []}

    def _add_stalled_object(
        self, new_object: StalledObject, stalled_list: StalledDicts
    ):
        object_type = type(new_object)
        if object_type not in stalled_list:
            stalled_list[object_type] = []
        stalled_list[object_type].append(new_object)

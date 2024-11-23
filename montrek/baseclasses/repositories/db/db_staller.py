from baseclasses.models import MontrekHubABC, MontrekSatelliteABC
from baseclasses.repositories.annotator import Annotator

StalledSatelliteDict = dict[type[MontrekSatelliteABC], list[MontrekSatelliteABC]]

StalledHubDict = dict[type[MontrekHubABC], list[MontrekHubABC]]


StalledObject = MontrekSatelliteABC | MontrekHubABC

StalledDicts = StalledSatelliteDict | StalledHubDict


class DbStaller:
    def __init__(self, annotator: Annotator):
        self.annotator = annotator
        self.new_satellites: StalledSatelliteDict = {
            sat_class: [] for sat_class in annotator.annotated_satellite_classes
        }
        self.hubs: StalledHubDict = {annotator.hub_class: []}

    def stall_hub(self, new_hub: MontrekHubABC):
        self._add_stalled_object(new_hub, self.hubs)

    def stall_new_satellite(self, new_satellite: MontrekSatelliteABC):
        self._add_stalled_object(new_satellite, self.new_satellites)

    def get_hubs(self) -> StalledHubDict:
        return self.hubs

    def get_new_satellites(self) -> StalledSatelliteDict:
        return self.new_satellites

    def _add_stalled_object(
        self, new_object: StalledObject, stalled_list: StalledDicts
    ):
        object_type = type(new_object)
        stalled_list[object_type].append(new_object)

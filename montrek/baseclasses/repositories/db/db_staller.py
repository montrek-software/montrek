from baseclasses.models import MontrekSatelliteABC, MontrekHubABC

StalledSatelliteDict = dict[type[MontrekSatelliteABC], list[MontrekSatelliteABC]]
StalledHubList = list[MontrekHubABC]


class DbStaller:
    def __init__(self):
        self.new_satellites: StalledSatelliteDict = {}
        self.hub_list: StalledHubList = []

    def stall_hub(self, new_hub: MontrekHubABC):
        self.hub_list.append(new_hub)

    def stall_new_satellite(self, new_satellite: MontrekSatelliteABC):
        sat_type = type(new_satellite)
        if sat_type not in self.new_satellites:
            self.new_satellites[sat_type] = []
        self.new_satellites[sat_type].append(new_satellite)

    def get_hubs(self) -> StalledHubList:
        return self.hub_list

    def get_new_satellites(self) -> StalledSatelliteDict:
        return self.new_satellites

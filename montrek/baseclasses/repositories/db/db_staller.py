from baseclasses.models import MontrekSatelliteABC

StalledSatelliteDict = dict[type[MontrekSatelliteABC], list[MontrekSatelliteABC]]


class DbStaller:
    def __init__(self):
        self.new_satellites: StalledSatelliteDict = {}

    def stall_new_satellite(self, new_satellite: MontrekSatelliteABC):
        sat_type = type(new_satellite)
        if sat_type not in self.new_satellites:
            self.new_satellites[sat_type] = []
        self.new_satellites[sat_type].append(new_satellite)

    def get_new_satellites(self) -> StalledSatelliteDict:
        return self.new_satellites

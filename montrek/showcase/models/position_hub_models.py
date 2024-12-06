from baseclasses.fields import HubForeignKey
from baseclasses.models import HubValueDate, MontrekHubABC


class PositionHub(MontrekHubABC):
    pass


class PositionHubValueDate(HubValueDate):
    hub = HubForeignKey(PositionHub)

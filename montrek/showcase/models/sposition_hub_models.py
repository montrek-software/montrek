from baseclasses.fields import HubForeignKey
from baseclasses.models import HubValueDate, MontrekHubABC


class SPositionHub(MontrekHubABC):
    pass


class SPositionHubValueDate(HubValueDate):
    hub = HubForeignKey(SPositionHub)

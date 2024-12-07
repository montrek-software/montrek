from baseclasses.fields import HubForeignKey
from baseclasses.models import HubValueDate, MontrekHubABC


class SProductHub(MontrekHubABC):
    pass


class SProductHubValueDate(HubValueDate):
    hub = HubForeignKey(SProductHub)

from baseclasses.fields import HubForeignKey
from baseclasses.models import HubValueDate, MontrekHubABC


class MontrekUserHub(MontrekHubABC):
    pass


class MontrekUserHubValueDate(HubValueDate):
    hub = HubForeignKey(MontrekUserHub)

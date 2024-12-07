from baseclasses.fields import HubForeignKey
from baseclasses.models import HubValueDate, MontrekHubABC


class SAssetHub(MontrekHubABC):
    pass


class SAssetHubValueDate(HubValueDate):
    hub = HubForeignKey(SAssetHub)

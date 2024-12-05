from baseclasses.fields import HubForeignKey
from baseclasses.models import HubValueDate, MontrekHubABC


class ProductHub(MontrekHubABC):
    pass


class ProductHubValueDate(HubValueDate):
    hub = HubForeignKey(ProductHub)

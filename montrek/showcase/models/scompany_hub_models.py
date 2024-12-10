from baseclasses.fields import HubForeignKey
from baseclasses.models import HubValueDate, MontrekHubABC


class SCompanyHub(MontrekHubABC):
    pass


class SCompanyHubValueDate(HubValueDate):
    hub = HubForeignKey(SCompanyHub)

from baseclasses.fields import HubForeignKey
from baseclasses.models import HubValueDate, MontrekHubABC


class CompanyHub(MontrekHubABC):
    pass


class CompanyHubValueDate(HubValueDate):
    hub = HubForeignKey(CompanyHub)

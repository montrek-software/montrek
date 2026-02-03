from baseclasses.fields import HubForeignKey
from baseclasses.models import HubValueDate, MontrekHubABC


class DownloadRegistryHub(MontrekHubABC):
    pass


class DownloadRegistryHubValueDate(HubValueDate):
    hub = HubForeignKey(DownloadRegistryHub)

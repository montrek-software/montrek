from baseclasses.fields import HubForeignKey
from baseclasses.models import HubValueDate, MontrekHubABC


class SftpConnectionHub(MontrekHubABC):
    pass


class SftpConnectionHubValueDate(HubValueDate):
    hub = HubForeignKey(SftpConnectionHub)

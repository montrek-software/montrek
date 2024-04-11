from baseclasses.managers.montrek_manager import MontrekManager
from montrek_example.repositories.hub_a_repository import HubARepository
from montrek_example.repositories.hub_b_repository import HubBRepository
from montrek_example.repositories.hub_c_repository import HubCRepository
from montrek_example.repositories.hub_d_repository import HubDRepository


class HubAManager(MontrekManager):
    repository_class = HubARepository


class HubBManager(MontrekManager):
    repository_class = HubBRepository


class HubCManager(MontrekManager):
    repository_class = HubCRepository


class HubDManager(MontrekManager):
    repository_class = HubDRepository

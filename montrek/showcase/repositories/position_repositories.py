from baseclasses.repositories.montrek_repository import MontrekRepository
from showcase.models.position_hub_models import PositionHub


class PositionRepository(MontrekRepository):
    hub_class = PositionHub

    def set_annotations(self):
        pass

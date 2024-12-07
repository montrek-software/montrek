from baseclasses.repositories.montrek_repository import MontrekRepository
from showcase.models.sposition_hub_models import SPositionHub


class SPositionRepository(MontrekRepository):
    hub_class = SPositionHub

    def set_annotations(self):
        pass

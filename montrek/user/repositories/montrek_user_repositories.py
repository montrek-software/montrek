from baseclasses.repositories.montrek_repository import MontrekRepository
from user.models.montrek_user_hub_models import MontrekUserHub


class MontrekUserRepository(MontrekRepository):
    hub_class = MontrekUserHub

    def set_annotations(self):
        pass

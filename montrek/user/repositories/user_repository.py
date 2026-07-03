from baseclasses.repositories.montrek_repository import MontrekRepository
from user.models import MontrekUser, UserAssignmentHub, UserAssignmentSatellite


class MontrekUserRepository:
    def receive(self):
        return MontrekUser.objects.all()


class UserAssignmentRepository(MontrekRepository):
    hub_class = UserAssignmentHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(UserAssignmentSatellite, ["user__email"])

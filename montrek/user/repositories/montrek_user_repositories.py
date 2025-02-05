from baseclasses.models import MontrekHubABC
from baseclasses.repositories.db.db_creator import DataDict
from baseclasses.repositories.montrek_repository import MontrekRepository
from user.models.montrek_user_hub_models import MontrekUserHub
from user.models.montrek_user_sat_models import MontrekUserSatellite


class MontrekUserRepository(MontrekRepository):
    hub_class = MontrekUserHub

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            MontrekUserSatellite, ["montrek_user_status"]
        )

    def create_by_dict(self, data: DataDict) -> MontrekHubABC:
        hub = super().create_by_dict(data)
        user = hub.created_by
        montrek_user_status = data.get("montrek_user_status")
        is_active = (
            montrek_user_status
            == MontrekUserSatellite.MontrekUserStatusChoices.ACTIVE.value
        )
        user.is_active = is_active
        user.save()

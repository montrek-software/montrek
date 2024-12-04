from baseclasses.repositories.montrek_repository import MontrekRepository
from montrek_example import models as me_models


class HubERepository(MontrekRepository):
    hub_class = me_models.HubE

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatE1,
            [
                "field_e1_str",
                "field_e1_float",
            ],
        )
        self.add_satellite_fields_annotations(
            me_models.SatE2,
            ["field_e2_str", "field_e2_int"],
        )

from montrek_example import models as me_models
from baseclasses.repositories.montrek_repository import MontrekRepository


class HubDRepository(MontrekRepository):
    hub_class = me_models.HubD

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatD1,
            ["field_d1_str", "field_d1_int"],
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatB1,
            me_models.LinkHubBHubD,
            ["field_b1_str"],
            reversed_link=True,
        )


class HubDRepositoryTSReverseLink(MontrekRepository):
    hub_class = me_models.HubD

    def set_annotations(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatTSC2,
            me_models.LinkHubCHubD,
            ["field_tsc2_float"],
            reversed_link=True,
        )

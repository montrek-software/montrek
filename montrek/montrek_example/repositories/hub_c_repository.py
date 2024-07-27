from montrek_example import models as me_models
from baseclasses.repositories.montrek_repository import MontrekRepository


class HubCRepository(MontrekRepository):
    hub_class = me_models.HubC

    def std_queryset(self):
        self.add_satellite_fields_annotations(
            me_models.SatTSC2,
            [
                "field_tsc2_float",
            ],
        )
        self.add_satellite_fields_annotations(
            me_models.SatTSC3,
            [
                "field_tsc3_int",
                "field_tsc3_str",
                "value_date",
            ],
        )
        self.add_satellite_fields_annotations(
            me_models.SatC1,
            [
                "field_c1_bool",
                "field_c1_str",
            ],
        )
        return self.build_queryset()

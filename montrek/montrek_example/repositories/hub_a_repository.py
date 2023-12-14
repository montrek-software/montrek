from montrek_example import models as me_models
from baseclasses.repositories.montrek_repository import MontrekRepository

class HubAMontrekRepository(MontrekRepository):
    hub_class = me_models.HubA

    def test_queryset_1(self):
        self.add_satellite_fields_annotations(
            me_models.SatA1,
            [
                "field_a1_int",
            ],
            self.reference_date,
        )
        self.add_satellite_fields_annotations(
            me_models.SatA2,
            [
                "field_a2_float",
            ],
            self.reference_date,
        )
        return self.build_queryset()

    def test_queryset_2(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatB1,
            me_models.LinkHubAHubB,
            ['field_b1_str'],
            self.reference_date,
        )
        return self.build_queryset()


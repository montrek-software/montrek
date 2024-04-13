from montrek_example import models as me_models
from montrek_example.repositories.hub_d_repository import HubDRepository
from baseclasses.repositories.montrek_repository import MontrekRepository


class HubBRepository(MontrekRepository):
    hub_class = me_models.HubB

    def std_queryset(self):
        self.add_satellite_fields_annotations(
            me_models.SatB1,
            [
                "field_b1_str",
                "field_b1_date",
            ],
        )
        self.add_satellite_fields_annotations(
            me_models.SatB2,
            ["field_b2_str", "field_b2_choice"],
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatD1,
            me_models.LinkHubBHubD,
            ["field_d1_str", "field_d1_int"],
        )
        self.add_satellite_fields_annotations(
            me_models.DataQualitySatB,
            [
                "data_quality_status",
                "data_quality_message",
            ],
        )
        return self.build_queryset()

    def test_queryset_1(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatA1,
            me_models.LinkHubAHubB,
            ["field_a1_int"],
            reversed_link=True,
        )
        return self.build_queryset()

    def get_hub_d_objects(self):
        return HubDRepository().std_queryset()

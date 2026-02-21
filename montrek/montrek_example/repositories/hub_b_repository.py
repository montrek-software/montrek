from montrek_example.models import example_models as me_models
from montrek_example.repositories.hub_d_repository import HubDRepository
from baseclasses.repositories.montrek_repository import MontrekRepository
from baseclasses.repositories.subquery_builder import CrossSatelliteFilter


class HubBRepository(MontrekRepository):
    hub_class = me_models.HubB

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatB1,
            [
                "field_b1_str",
                "field_b1_date",
                "alert_level",
                "alert_message",
            ],
        )
        self.add_satellite_fields_annotations(
            me_models.SatB2,
            ["field_b2_str", "field_b2_choice"],
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatD1,
            me_models.LinkHubBHubD,
            ["hub_entity_id", "field_d1_str", "field_d1_int"],
            rename_field_map={"hub_entity_id": "hub_d_id"},
            separator=",",
        )

    def get_hub_d_objects(self):
        return HubDRepository().receive()


class HubBRepository2(MontrekRepository):
    hub_class = me_models.HubB

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatB1,
            [
                "field_b1_str",
            ],
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatA1,
            me_models.LinkHubAHubB,
            ["field_a1_int"],
            reversed_link=True,
        )


class HubBRepositoryWithCrossSatFilter(MontrekRepository):
    """HubB repository that fetches SatD1.field_d1_str via LinkHubBHubD,
    filtered to only include HubDs that have a linked HubC (via LinkHubCHubD)
    with a matching SatC1 record."""

    hub_class = me_models.HubB

    def set_annotations(self):
        self.add_satellite_fields_annotations(me_models.SatB1, ["field_b1_str"])
        self.add_linked_satellites_field_annotations(
            me_models.SatD1,
            me_models.LinkHubBHubD,
            ["field_d1_str"],
            cross_satellite_filters=(
                CrossSatelliteFilter(
                    satellite_class=me_models.SatC1,
                    link_class=me_models.LinkHubCHubD,
                    filter_dict={"field_c1_str": "matched"},
                    reversed_link=True,
                ),
            ),
        )

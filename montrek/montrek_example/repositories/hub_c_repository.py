from baseclasses.repositories.montrek_repository import MontrekRepository
from montrek_example.models import example_models as me_models
from montrek_example.repositories.hub_d_repository import HubDRepository


class HubCRepository(MontrekRepository):
    hub_class = me_models.HubC

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatTSC2,
            ["field_tsc2_float", "created_by__email"],
        )
        self.add_satellite_fields_annotations(
            me_models.SatTSC3,
            [
                "field_tsc3_int",
                "field_tsc3_str",
            ],
        )
        self.add_satellite_fields_annotations(
            me_models.SatTSC4,
            [
                "field_tsc4_int",
            ],
        )
        self.add_satellite_fields_annotations(
            me_models.SatC1,
            [
                "field_c1_bool",
                "field_c1_str",
            ],
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatD1,
            me_models.LinkHubCHubD,
            ["field_d1_str"],
            separator=",",
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatD1,
            me_models.LinkHubCHubD,
            ["field_d1_int"],
            agg_func="sum",
            link_satellite_filter={"field_d1_int__lte": 6},
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatTSD2,
            me_models.LinkHubCHubD,
            ["field_tsd2_float", "field_tsd2_int"],
            link_satellite_filter={"field_tsd2_float__gte": 0},
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatTSD2,
            me_models.LinkHubCHubD,
            ["field_tsd2_float"],
            rename_field_map={"field_tsd2_float": "field_tsd2_float_agg"},
            link_satellite_filter={"field_tsd2_float__gte": 0},
            agg_func="sum",
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatTSD2,
            me_models.LinkHubCHubD,
            ["field_tsd2_float"],
            rename_field_map={"field_tsd2_float": "field_tsd2_float_latest"},
            agg_func="latest",
            link_satellite_filter={"field_tsd2_float__gte": 0},
        )

    def get_hub_d_objects(self):
        return HubDRepository().receive()


class HubCRepositoryLastTS(HubCRepository):
    latest_ts = True


class HubCRepositorySumTS(MontrekRepository):
    hub_class = me_models.HubC
    latest_ts = True

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatTSC2,
            ["field_tsc2_float"],
            rename_field_map={"field_tsc2_float": "agg_field_tsc2_float"},
            ts_agg_func="sum",
        )
        self.add_satellite_fields_annotations(
            me_models.SatC1,
            [
                "field_c1_bool",
                "field_c1_str",
            ],
        )


class HubCRepositoryOnlyStatic(MontrekRepository):
    hub_class = me_models.HubC

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatC1,
            [
                "field_c1_bool",
                "field_c1_str",
            ],
        )


class HubCRepository2(MontrekRepository):
    hub_class = me_models.HubC

    def set_annotations(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatA1,
            me_models.LinkHubAHubC,
            ["field_a1_int"],
            reversed_link=True,
        )


class HubCRepositoryCommonFields(MontrekRepository):
    hub_class = me_models.HubC

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatTSC2,
            ["field_tsc2_float", "comment"],
            rename_field_map={"comment": "comment_tsc2"},
        )
        self.add_satellite_fields_annotations(
            me_models.SatC1,
            [
                "field_c1_bool",
                "field_c1_str",
                "comment",
            ],
            rename_field_map={"comment": "comment_c1"},
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatD1,
            me_models.LinkHubCHubD,
            ["field_d1_str", "comment"],
            rename_field_map={"comment": "comment_d1"},
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatTSD2,
            me_models.LinkHubCHubD,
            ["field_tsd2_float", "field_tsd2_int", "comment"],
            rename_field_map={"comment": "comment_tsd2"},
        )


class HubCRepositoryLast(MontrekRepository):
    hub_class = me_models.HubC

    def set_annotations(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatD1,
            me_models.LinkHubCHubD,
            ["field_d1_int"],
            agg_func="latest",
        )


class HubCRepositoryMean(MontrekRepository):
    hub_class = me_models.HubC

    def set_annotations(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatD1,
            me_models.LinkHubCHubD,
            ["field_d1_int"],
            agg_func="mean",
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatA2,
            me_models.LinkHubAHubC,
            ["field_a2_float"],
            reversed_link=True,
            agg_func="mean",
        )


class HubCRepositoryCount(MontrekRepository):
    hub_class = me_models.HubC

    def set_annotations(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatD1,
            me_models.LinkHubCHubD,
            ["field_d1_int"],
            agg_func="count",
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatA2,
            me_models.LinkHubAHubC,
            ["field_a2_float"],
            reversed_link=True,
            agg_func="count",
            link_satellite_filter={"field_a2_float__gte": 2.6},
            rename_field_map={"field_a2_float": "a2_counter_w_filter"},
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatA2,
            me_models.LinkHubAHubC,
            ["field_a2_float"],
            reversed_link=True,
            agg_func="count",
            rename_field_map={"field_a2_float": "a2_counter"},
        )


class HubCRepositoryReversedParents(MontrekRepository):
    hub_class = me_models.HubC

    def set_annotations(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatB1,
            me_models.LinkHubAHubB,
            ["field_b1_str"],
            parent_link_classes=(me_models.LinkHubAHubC,),
            parent_link_reversed=(True,),
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatA1,
            me_models.LinkHubAHubC,
            ["field_a1_str"],
            reversed_link=True,
        )


class HubCRepositoryReversedParentsNoMatchingReversedParents(MontrekRepository):
    hub_class = me_models.HubC

    def set_annotations(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatB1,
            me_models.LinkHubAHubB,
            ["field_b1_str"],
            parent_link_classes=(me_models.LinkHubAHubC,),
            parent_link_reversed=(True, False),
        )


class HubCRepositoryWithManyToManyParents(MontrekRepository):
    hub_class = me_models.HubC

    def set_annotations(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatE1,
            me_models.LinkHubDHubE,
            ["field_e1_str"],
            parent_link_classes=(me_models.LinkHubCHubD,),
        )


class HubCRepositoryViewModel(MontrekRepository):
    hub_class = me_models.HubC

    def set_annotations(self):
        self.add_satellite_fields_annotations(
            me_models.SatTSC2,
            ["field_tsc2_float"],
        )

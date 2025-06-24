from django.utils import timezone
from montrek_example.models import example_models as me_models
from baseclasses.repositories.montrek_repository import MontrekRepository


class HubDRepository(MontrekRepository):
    hub_class = me_models.HubD

    def set_annotations(self):
        self.session_data["start_date"] = timezone.datetime.min
        self.session_data["end_date"] = timezone.datetime.max
        self.add_satellite_fields_annotations(
            me_models.SatD1,
            ["field_d1_str", "field_d1_int"],
        )
        self.add_satellite_fields_annotations(
            me_models.SatTSD2,
            ["field_tsd2_float", "field_tsd2_int"],
        )
        self.add_linked_satellites_field_annotations(
            me_models.SatB1,
            me_models.LinkHubBHubD,
            ["hub_entity_id", "field_b1_str"],
            reversed_link=True,
            rename_field_map={"hub_entity_id": "hub_b_id"},
            separator=",",
        )


class HubDRepositoryTSReverseLink(MontrekRepository):
    hub_class = me_models.HubD

    def set_annotations(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatTSC2,
            me_models.LinkHubCHubD,
            ["field_tsc2_float"],
            reversed_link=True,
            separator=",",
        )


class HubDRepositoryReversedParentLink(MontrekRepository):
    hub_class = me_models.HubD

    def set_annotations(self):
        self.add_linked_satellites_field_annotations(
            me_models.SatA1,
            me_models.LinkHubAHubC,
            ["field_a1_str"],
            parent_link_classes=(me_models.LinkHubCHubD,),
            reversed_link=True,
        )
